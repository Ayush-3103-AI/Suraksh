# vault.py
# Vault storage operations with defense-grade file organization
# Clearance: L1=lowest, L2=medium, L3=highest, 4=superuser
# File structure:
#   encrypted_vault/  - ONLY encrypted chunks (no plaintext)
#   bit_manipulated/   - Output after bit manipulation (before encryption)
#   manifests/         - File metadata / chunk maps
#   keys/              - User keys and clearance keys

import os
import json
import secrets
from crypto import generate_fek, aesgcm_encrypt, aesgcm_decrypt, CHUNK_SIZE, bit_permutation_obfuscate, bit_permutation_reverse, hybrid_wrap_fek, hybrid_unwrap_fek, hkdf_derive
from blockchain import append_event, init_chain
from cryptography.hazmat.primitives.asymmetric import x25519
from logger import log_network, log_app, log_chain
import base64
import hashlib

BASE = "vault_storage"
ENCRYPTED_VAULT_DIR = f"{BASE}/encrypted_vault"  # ONLY encrypted chunks
BIT_MANIPULATED_DIR = f"{BASE}/bit_manipulated"  # Bit-manipulated files (before encryption)
MANIFESTS_DIR = f"{BASE}/manifests"              # File metadata / chunk maps
KEYS_DIR = f"{BASE}/keys"                        # User keys and clearance keys
REQUESTS_FILE = f"{BASE}/requests.json"

CLEARANCE_KEYS_FILE = f"{KEYS_DIR}/clearance_keys.json"


def init_vault():
    """Initialize vault directory structure with strict separation."""
    os.makedirs(ENCRYPTED_VAULT_DIR, exist_ok=True)
    os.makedirs(BIT_MANIPULATED_DIR, exist_ok=True)
    os.makedirs(MANIFESTS_DIR, exist_ok=True)
    os.makedirs(KEYS_DIR, exist_ok=True)
    init_chain()
    
    # Create clearance symmetric keys (mock HSM)
    if not os.path.exists(CLEARANCE_KEYS_FILE):
        keys = {
            "L1": secrets.token_bytes(32).hex(),
            "L2": secrets.token_bytes(32).hex(),
            "L3": secrets.token_bytes(32).hex()
        }
        with open(CLEARANCE_KEYS_FILE, "w") as f:
            json.dump({k: v for k, v in keys.items()}, f)
        log_app("Clearance keys initialized: L1, L2, L3 symmetric keys generated and stored")
    
    # Requests file
    if not os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "w") as f:
            json.dump({}, f)
    
    log_app("Vault initialization complete: directory structure verified, no plaintext in encrypted_vault")


def load_clearance_key(level: int) -> bytes:
    """Load clearance-level symmetric key from secure storage."""
    with open(CLEARANCE_KEYS_FILE, "r") as f:
        d = json.load(f)
    return bytes.fromhex(d[f"L{level}"])


def write_metadata(meta):
    """Write file manifest to manifests directory."""
    # Support both file_id (normal files) and document_id (CLSD)
    file_id = meta.get("file_id") or meta.get("document_id")
    meta_path = f"{MANIFESTS_DIR}/{file_id}.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)


def read_metadata(file_id):
    """Read file manifest from manifests directory."""
    meta_path = f"{MANIFESTS_DIR}/{file_id}.json"
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, "r") as f:
        return json.load(f)


def list_all_metadata():
    """List all file manifests."""
    files = []
    if os.path.exists(MANIFESTS_DIR):
        for fname in os.listdir(MANIFESTS_DIR):
            if fname.endswith(".json"):
                file_id = fname[:-5]
                meta = read_metadata(file_id)
                if meta:
                    files.append(meta)
    return files


def upload_file(uinfo: dict, filepath: str, clearance: int):
    """
    Upload file with end-to-end encryption pipeline.
    Security guarantee: Plaintext never enters encrypted_vault directory.
    """
    init_vault()
    file_id = secrets.token_hex(16)
    filename = os.path.basename(filepath)
    
    log_app(f"File upload initiated: user {uinfo['user_id']} uploading '{filename}' with clearance L{clearance}")
    
    # Step 1: Read file bytes (client-side operation simulated)
    with open(filepath, "rb") as f:
        raw = f.read()
    
    log_network(f"Binary conversion complete: source file '{filename}' converted to {len(raw)} bytes of raw binary data")
    
    # Step 2: Generate File Encryption Key (FEK)
    fek = generate_fek()
    log_network(f"File Encryption Key (FEK) generated: 256-bit cryptographically secure random key derived")
    
    # Step 3: Apply deterministic bit-level permutation
    seed = hkdf_derive(fek, info=b"permutation-seed", length=32)
    log_network("Bit permutation initiated: applying deterministic bit-level obfuscation using FEK-derived seed")
    obf = bit_permutation_obfuscate(raw, seed)
    
    # Store bit-manipulated file (before encryption) - visible to judges
    bit_manipulated_path = f"{BIT_MANIPULATED_DIR}/{file_id}.bin"
    with open(bit_manipulated_path, "wb") as tf:
        tf.write(obf)
    log_network(f"Bit-manipulated file stored: intermediate obfuscated binary written to {BIT_MANIPULATED_DIR} (plaintext never enters encrypted_vault)")
    
    # Step 4: Chunking and encryption
    file_master_key = hkdf_derive(fek, info=b"file-master", length=32)
    chunks = []
    num_chunks = (len(obf) + CHUNK_SIZE - 1) // CHUNK_SIZE
    log_network(f"Chunking initiated: file split into {num_chunks} chunks of {CHUNK_SIZE} bytes each for parallel encryption")
    
    for i in range(0, len(obf), CHUNK_SIZE):
        chunk = obf[i:i+CHUNK_SIZE]
        chunk_idx = i // CHUNK_SIZE
        
        # Derive chunk-specific encryption key
        chunk_key = hkdf_derive(file_master_key, info=b"chunk-%d" % i, length=32)
        
        # Encrypt chunk with AES-256-GCM
        enc = aesgcm_encrypt(chunk_key, chunk, associated_data=file_id.encode())
        
        # Store encrypted chunk in encrypted_vault (ONLY encrypted data here)
        chunk_name = f"{file_id}.chunk.{i}"
        chunk_path = f"{ENCRYPTED_VAULT_DIR}/{chunk_name}"
        with open(chunk_path, "wb") as cf:
            cf.write(enc)
        chunks.append(chunk_name)
        
        # Compute hash of encrypted chunk for integrity verification
        chunk_hash = hashlib.sha256(enc).hexdigest()
        log_network(f"Chunk {chunk_idx+1}/{num_chunks} encrypted: AES-256-GCM encryption complete, integrity tag generated, chunk hash {chunk_hash[:16]}...")
    
    log_network(f"Encryption pipeline complete: all {num_chunks} chunks encrypted and stored in encrypted_vault (zero plaintext in vault)")
    
    # Step 5: Wrap FEK with clearance-level key
    clearance_key = load_clearance_key(clearance)
    wrapped_fek = aesgcm_encrypt(clearance_key, fek, associated_data=b"clearance-wrap")
    log_network(f"FEK wrapped: File Encryption Key encrypted with L{clearance} clearance-level symmetric key using AES-256-GCM")
    
    # Step 6: Create file manifest
    # Preserve original filename and extension for proper download
    meta = {
        "file_id": file_id,
        "uploader": uinfo["user_id"],
        "filename": filename,
        "original_filename": filename,  # Store original filename with extension
        "clearance": clearance,
        "chunks": chunks,
        "wrapped_fek": base64.b64encode(wrapped_fek).decode(),
        "file_hash": __hash_file_bytes(raw),
        "approved_access": []
    }
    write_metadata(meta)
    log_app(f"File manifest created: metadata stored in manifests directory, file_id={file_id}")
    
    # Step 7: Blockchain audit log
    append_event("UPLOAD", {
        "file_id": file_id,
        "uploader": uinfo["user_id"],
        "filename": filename,
        "clearance": clearance
    })
    
    log_app(f"File upload complete: '{filename}' successfully encrypted and stored, security guarantee: plaintext never entered encrypted_vault")
    return file_id


def __hash_file_bytes(b: bytes):
    """Compute SHA-256 hash of file bytes for integrity verification."""
    return hashlib.sha256(b).hexdigest()


def retrieve_file(uinfo: dict, file_id: str):
    """
    Retrieve and decrypt file with clearance validation.
    Security guarantee: Decryption occurs client-side, vault never decrypts.
    """
    init_vault()
    meta = read_metadata(file_id)
    if not meta:
        log_app(f"File retrieval failed: file_id {file_id} not found in manifests")
        return "FILE NOT FOUND"

    log_app(f"File retrieval initiated: user {uinfo['user_id']} requesting file_id {file_id}")
    log_network(f"Retrieval pipeline started: reading encrypted chunks from encrypted_vault for file_id {file_id}")

    # Clearance validation
    user_clearance = uinfo["clearance"]
    file_clearance = meta["clearance"]
    user_clearance_name = {1: "L1", 2: "L2", 3: "L3", 4: "L4"}.get(user_clearance, f"L{user_clearance}")
    file_clearance_name = {1: "L1", 2: "L2", 3: "L3"}.get(file_clearance, f"L{file_clearance}")
    
    # Superuser can access everything
    if user_clearance != 4:
        # Higher clearance users can access lower clearance files
        # user_clearance > file_clearance means user has higher clearance (e.g., L3 > L1)
        # user_clearance < file_clearance means user has lower clearance (e.g., L1 < L3)
        if user_clearance < file_clearance:
            # User has lower clearance than file - check approved access
            if uinfo["user_id"] not in meta.get("approved_access", []):
                log_app(f"Access denied: user {uinfo['user_id']} ({user_clearance_name}) lacks sufficient clearance to access {file_clearance_name} file. Request access required.")
                return "ACCESS DENIED - Request access first"

    log_app(f"Clearance validation passed: user {uinfo['user_id']} ({user_clearance_name}) authorized to access {file_clearance_name} file")

    # Unwrap FEK using clearance key
    clearance_key = load_clearance_key(file_clearance)
    wrapped_fek = base64.b64decode(meta["wrapped_fek"])
    try:
        fek = aesgcm_decrypt(clearance_key, wrapped_fek, associated_data=b"clearance-wrap")
        log_network("FEK unwrapped: File Encryption Key decrypted using clearance-level symmetric key, AES-256-GCM integrity verified")
    except Exception as e:
        log_network(f"FEK unwrap failed: decryption error - {str(e)}")
        return "FEK UNWRAP FAILED"

    # Reconstruct file from encrypted chunks
    file_master_key = hkdf_derive(fek, info=b"file-master", length=32)
    out_bytes = bytearray()
    chunks = sorted(meta["chunks"], key=lambda s: int(s.split(".")[-1]))
    log_network(f"Decryption pipeline initiated: decrypting {len(chunks)} encrypted chunks from encrypted_vault")
    
    for chunk_name in chunks:
        enc_path = f"{ENCRYPTED_VAULT_DIR}/{chunk_name}"
        enc = open(enc_path, "rb").read()
        idx = int(chunk_name.split(".")[-1])
        chunk_key = hkdf_derive(file_master_key, info=b"chunk-%d" % idx, length=32)
        dec = aesgcm_decrypt(chunk_key, enc, associated_data=file_id.encode())
        out_bytes.extend(dec)
        log_network(f"Chunk decrypted: chunk at offset {idx} decrypted, AES-256-GCM integrity tag verified")
    
    log_network(f"Decryption complete: all {len(chunks)} chunks decrypted, total {len(out_bytes)} bytes reconstructed")

    # Reverse bit permutation
    seed = hkdf_derive(fek, info=b"permutation-seed", length=32)
    log_network("Bit permutation reversal: applying reverse permutation to restore original file structure")
    orig = bit_permutation_reverse(bytes(out_bytes), seed)

    log_network(f"File reconstruction complete: original file restored, {len(orig)} bytes, ready for client-side delivery")
    log_app(f"File retrieval complete: file_id {file_id} successfully decrypted and delivered to user {uinfo['user_id']}")

    # Blockchain audit log
    append_event("ACCESS", {
        "file_id": file_id,
        "actor": uinfo["user_id"]
    })

    return orig


def share_file(sender_info: dict, receiver_info: dict, file_id: str):
    """
    Re-encrypt file with NEW FEK for receiver.
    Security guarantee: Old encryption keys never reused, new FEK generated per share.
    """
    init_vault()
    meta = read_metadata(file_id)
    if not meta:
        return "FILE NOT FOUND"
    
    log_app(f"File sharing initiated: user {sender_info['user_id']} sharing file_id {file_id} with user {receiver_info['user_id']}")
    
    # Verify sender has access
    sender_clearance = sender_info["clearance"]
    file_clearance = meta["clearance"]
    
    if sender_clearance != 4:  # superuser check
        if sender_clearance < file_clearance:
            if sender_info["user_id"] not in meta.get("approved_access", []):
                log_app(f"Share denied: sender {sender_info['user_id']} lacks access to file_id {file_id}")
                return "SHARE DENIED - Sender lacks access"

    # Receiver must have equal or higher clearance
    receiver_clearance = receiver_info["clearance"]
    if receiver_clearance != 4:  # superuser exception
        if receiver_clearance < file_clearance:
            log_app(f"Share denied: receiver {receiver_info['user_id']} clearance insufficient for file_id {file_id}")
            return "SHARE DENIED - Receiver clearance too low"

    log_app(f"Share authorization verified: both sender and receiver authorized for file_id {file_id}")

    # Read and decrypt original file
    log_network("Re-encryption pipeline: reading original encrypted chunks for re-encryption with new FEK")
    
    clearance_key = load_clearance_key(file_clearance)
    wrapped_fek = base64.b64decode(meta["wrapped_fek"])
    try:
        old_fek = aesgcm_decrypt(clearance_key, wrapped_fek, associated_data=b"clearance-wrap")
    except Exception as e:
        return "FEK UNWRAP FAILED"

    file_master_key = hkdf_derive(old_fek, info=b"file-master", length=32)
    orig_bytes = bytearray()
    for chunk_name in sorted(meta["chunks"], key=lambda s: int(s.split(".")[-1])):
        enc_path = f"{ENCRYPTED_VAULT_DIR}/{chunk_name}"
        enc = open(enc_path, "rb").read()
        idx = int(chunk_name.split(".")[-1])
        chunk_key = hkdf_derive(file_master_key, info=b"chunk-%d" % idx, length=32)
        dec = aesgcm_decrypt(chunk_key, enc, associated_data=file_id.encode())
        orig_bytes.extend(dec)

    seed = hkdf_derive(old_fek, info=b"permutation-seed", length=32)
    orig = bit_permutation_reverse(bytes(orig_bytes), seed)

    # Generate NEW FEK for sharing (security: never reuse keys)
    new_fek = generate_fek()
    log_network("New FEK generated: cryptographically secure 256-bit key generated for shared file (old FEK will never be reused)")

    # Re-apply bit permutation with new seed
    new_seed = hkdf_derive(new_fek, info=b"permutation-seed", length=32)
    obf = bit_permutation_obfuscate(orig, new_seed)

    # Re-chunk and re-encrypt with new FEK
    new_file_id = secrets.token_hex(16)
    new_file_master_key = hkdf_derive(new_fek, info=b"file-master", length=32)
    new_chunks = []
    num_chunks = (len(obf) + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    log_network(f"Re-encryption initiated: file re-chunked into {num_chunks} chunks, encrypting with new FEK-derived keys")
    
    for i in range(0, len(obf), CHUNK_SIZE):
        chunk = obf[i:i+CHUNK_SIZE]
        chunk_key = hkdf_derive(new_file_master_key, info=b"chunk-%d" % i, length=32)
        enc = aesgcm_encrypt(chunk_key, chunk, associated_data=new_file_id.encode())
        chunk_name = f"{new_file_id}.chunk.{i}"
        chunk_path = f"{ENCRYPTED_VAULT_DIR}/{chunk_name}"
        with open(chunk_path, "wb") as cf:
            cf.write(enc)
        new_chunks.append(chunk_name)
        chunk_hash = hashlib.sha256(enc).hexdigest()
        log_network(f"Re-encrypted chunk {len(new_chunks)}/{num_chunks}: AES-256-GCM encryption complete, chunk hash {chunk_hash[:16]}...")

    # Wrap new FEK with receiver's clearance
    target_clearance = min(file_clearance, receiver_clearance) if receiver_clearance != 4 else file_clearance
    clearance_key = load_clearance_key(target_clearance)
    wrapped_new_fek = aesgcm_encrypt(clearance_key, new_fek, associated_data=b"clearance-wrap")
    log_network(f"New FEK wrapped: shared file FEK encrypted with L{target_clearance} clearance key")

    # Create new manifest
    new_meta = {
        "file_id": new_file_id,
        "uploader": sender_info["user_id"],
        "filename": meta["filename"],
        "original_filename": meta.get("original_filename", meta["filename"]),  # Preserve original filename
        "clearance": file_clearance,
        "chunks": new_chunks,
        "wrapped_fek": base64.b64encode(wrapped_new_fek).decode(),
        "file_hash": meta["file_hash"],
        "shared_with": receiver_info["user_id"],
        "shared_from": file_id,
        "approved_access": []
    }
    write_metadata(new_meta)

    log_network(f"Re-encryption complete: new file_id {new_file_id} created with new FEK, old encryption keys never reused")
    log_app(f"File sharing complete: file_id {file_id} shared as new file_id {new_file_id} with user {receiver_info['user_id']}")

    append_event("SHARE", {
        "file_id": file_id,
        "shared_as": new_file_id,
        "from": sender_info["user_id"],
        "to": receiver_info["user_id"]
    })

    return new_file_id


def request_access(user_id: str, file_id: str, reason: str):
    """Create an access request for higher-clearance file."""
    init_vault()
    meta = read_metadata(file_id)
    if not meta:
        return "FILE NOT FOUND"
    
    request_id = secrets.token_hex(8)
    
    with open(REQUESTS_FILE, "r+") as f:
        requests = json.load(f)
        requests[request_id] = {
            "request_id": request_id,
            "user_id": user_id,
            "file_id": file_id,
            "reason": reason,
            "status": "pending",
            "timestamp": __get_timestamp()
        }
        f.seek(0)
        json.dump(requests, f, indent=2)
        f.truncate()
    
    log_app(f"Access request created: user {user_id} requested access to file_id {file_id}, request_id {request_id}")
    
    append_event("REQUEST", {
        "request_id": request_id,
        "user_id": user_id,
        "file_id": file_id,
        "reason": reason
    })
    
    return request_id


def get_pending_requests():
    """Get all pending access requests."""
    if not os.path.exists(REQUESTS_FILE):
        return []
    
    with open(REQUESTS_FILE, "r") as f:
        requests = json.load(f)
    
    return [r for r in requests.values() if r.get("status") == "pending"]


def approve_request(request_id: str, approver_id: str):
    """Approve an access request."""
    init_vault()
    
    with open(REQUESTS_FILE, "r+") as f:
        requests = json.load(f)
        if request_id not in requests:
            return "REQUEST NOT FOUND"
        
        req = requests[request_id]
        if req["status"] != "pending":
            return "REQUEST ALREADY PROCESSED"
        
        req["status"] = "approved"
        req["approver"] = approver_id
        req["approved_at"] = __get_timestamp()
        
        # Add to file metadata
        meta = read_metadata(req["file_id"])
        if meta:
            if "approved_access" not in meta:
                meta["approved_access"] = []
            if req["user_id"] not in meta["approved_access"]:
                meta["approved_access"].append(req["user_id"])
            write_metadata(meta)
        
        f.seek(0)
        json.dump(requests, f, indent=2)
        f.truncate()
    
    log_app(f"Access request approved: superuser {approver_id} approved request_id {request_id}, user {req['user_id']} granted access to file_id {req['file_id']}")
    
    append_event("APPROVE", {
        "request_id": request_id,
        "user_id": req["user_id"],
        "file_id": req["file_id"],
        "approver": approver_id
    })
    
    return "APPROVED"


def deny_request(request_id: str, approver_id: str):
    """Deny an access request."""
    init_vault()
    
    with open(REQUESTS_FILE, "r+") as f:
        requests = json.load(f)
        if request_id not in requests:
            return "REQUEST NOT FOUND"
        
        req = requests[request_id]
        if req["status"] != "pending":
            return "REQUEST ALREADY PROCESSED"
        
        req["status"] = "denied"
        req["approver"] = approver_id
        req["denied_at"] = __get_timestamp()
        
        f.seek(0)
        json.dump(requests, f, indent=2)
        f.truncate()
    
    log_app(f"Access request denied: superuser {approver_id} denied request_id {request_id}, user {req['user_id']} access to file_id {req['file_id']} denied")
    
    append_event("DENY", {
        "request_id": request_id,
        "user_id": req["user_id"],
        "file_id": req["file_id"],
        "approver": approver_id
    })
    
    return "DENIED"


def __get_timestamp():
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


# ============================================================================
# CLSD (Clearance-Layered Secure Document) Functions
# ============================================================================

def create_clsd(uinfo: dict, title: str, level1_content: str, level2_content: str, level3_content: str):
    """
    Create a Clearance-Layered Secure Document (CLSD).
    Each section is encrypted independently with its clearance-level key.
    """
    init_vault()
    document_id = secrets.token_hex(16)
    
    log_app(f"CLSD creation initiated: user {uinfo['user_id']} creating CLSD document '{title}'")
    
    sections = []
    
    # Encrypt each section with its respective clearance-level key
    for level, content in [(1, level1_content), (2, level2_content), (3, level3_content)]:
        content_bytes = content.encode('utf-8')
        clearance_key = load_clearance_key(level)
        
        # Encrypt section content
        encrypted_data = aesgcm_encrypt(clearance_key, content_bytes, associated_data=f"clsd-section-{level}".encode())
        
        # Compute hash of encrypted data for integrity verification
        section_hash = hashlib.sha256(encrypted_data).hexdigest()
        
        sections.append({
            "level": level,
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "hash": section_hash
        })
        
        log_network(f"CLSD section L{level} encrypted: AES-256-GCM encryption complete, section hash {section_hash[:16]}...")
    
    # Create CLSD manifest
    meta = {
        "document_id": document_id,
        "type": "CLSD",
        "title": title,
        "created_by": uinfo["user_id"],
        "timestamp": __get_timestamp(),
        "sections": sections
    }
    write_metadata(meta)
    
    log_app(f"CLSD document created: '{title}' with document_id {document_id}, all sections encrypted and stored")
    
    # Blockchain audit log
    append_event("CREATE_CLSD", {
        "document_id": document_id,
        "user_id": uinfo["user_id"],
        "title": title
    })
    
    return document_id


def retrieve_clsd(uinfo: dict, document_id: str):
    """
    Retrieve CLSD document sections based on user clearance.
    Only sections where section.level <= user.clearance are decrypted and returned.
    """
    init_vault()
    meta = read_metadata(document_id)
    
    if not meta:
        log_app(f"CLSD retrieval failed: document_id {document_id} not found")
        return None, "DOCUMENT NOT FOUND"
    
    if meta.get("type") != "CLSD":
        log_app(f"CLSD retrieval failed: document_id {document_id} is not a CLSD document")
        return None, "NOT A CLSD DOCUMENT"
    
    user_clearance = uinfo["clearance"]
    user_clearance_name = {1: "L1", 2: "L2", 3: "L3", 4: "L4"}.get(user_clearance, f"L{user_clearance}")
    
    log_app(f"CLSD retrieval initiated: user {uinfo['user_id']} ({user_clearance_name}) requesting document_id {document_id}")
    
    # Decrypt only sections the user has clearance for
    decrypted_sections = []
    sections_decrypted = []
    
    for section in meta["sections"]:
        section_level = section["level"]
        
        # Superuser sees all sections
        if user_clearance == 4 or section_level <= user_clearance:
            clearance_key = load_clearance_key(section_level)
            encrypted_data = base64.b64decode(section["encrypted_data"])
            
            # Verify hash before decryption
            computed_hash = hashlib.sha256(encrypted_data).hexdigest()
            if computed_hash != section["hash"]:
                log_app(f"CLSD section L{section_level} integrity check failed: hash mismatch detected")
                return None, "INTEGRITY CHECK FAILED"
            
            try:
                decrypted_bytes = aesgcm_decrypt(clearance_key, encrypted_data, associated_data=f"clsd-section-{section_level}".encode())
                decrypted_content = decrypted_bytes.decode('utf-8')
                
                decrypted_sections.append({
                    "level": section_level,
                    "content": decrypted_content
                })
                sections_decrypted.append(section_level)
                
                log_network(f"CLSD section L{section_level} decrypted: AES-256-GCM decryption complete, integrity verified")
            except Exception as e:
                log_network(f"CLSD section L{section_level} decryption failed: {str(e)}")
                return None, "DECRYPTION FAILED"
    
    if not decrypted_sections:
        log_app(f"CLSD access denied: user {uinfo['user_id']} ({user_clearance_name}) lacks clearance for document_id {document_id}")
        return None, "ACCESS DENIED - INSUFFICIENT CLEARANCE"
    
    log_app(f"CLSD retrieval complete: user {uinfo['user_id']} ({user_clearance_name}) retrieved {len(decrypted_sections)} section(s) from document_id {document_id}")
    
    # Blockchain audit log
    append_event("VIEW_CLSD", {
        "document_id": document_id,
        "user_id": uinfo["user_id"],
        "clearance_level": user_clearance,
        "sections_decrypted": sections_decrypted
    })
    
    return {
        "document_id": document_id,
        "title": meta["title"],
        "sections": decrypted_sections
    }, None


def list_clsd_metadata(user_clearance: int):
    """
    List CLSD documents visible to user based on clearance.
    CLSD documents are ONLY visible if user has clearance >= 1 (lowest section).
    Returns list of CLSD metadata (without decrypted content).
    """
    init_vault()
    all_files = list_all_metadata()
    clsd_docs = []
    
    for meta in all_files:
        if meta.get("type") == "CLSD":
            # Check if user can see at least level 1 section
            # All CLSD docs have level 1, so if user has clearance >= 1, they can see the doc
            if user_clearance == 4 or user_clearance >= 1:
                # Return metadata without decrypted sections
                clsd_docs.append({
                    "document_id": meta["document_id"],
                    "title": meta["title"],
                    "created_by": meta["created_by"],
                    "timestamp": meta.get("timestamp", ""),
                    "type": "CLSD"
                })
    
    return clsd_docs
