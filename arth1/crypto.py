# crypto.py
# Crypto primitives: FEK generation, AES-GCM encrypt/decrypt, hybrid wrapping (X25519 + mocked PQC)
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import secrets
from bitarray import bitarray
import json
import hashlib
from logger import log_network

CHUNK_SIZE = 4096

def generate_fek():
    """Generate 256-bit File Encryption Key using cryptographically secure random number generator."""
    fek = secrets.token_bytes(32)  # 256-bit FEK
    return fek

def aesgcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b''):
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aes.encrypt(nonce, plaintext, associated_data)
    return nonce + ct

def aesgcm_decrypt(key: bytes, blob: bytes, associated_data: bytes = b''):
    aes = AESGCM(key)
    nonce = blob[:12]
    ct = blob[12:]
    return aes.decrypt(nonce, ct, associated_data)

def hkdf_derive(key_material: bytes, salt: bytes = b'', info: bytes = b'', length: int = 32):
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info
    )
    return hkdf.derive(key_material)

# Hybrid wrapping: combine X25519 shared secret + mocked PQC secret into a single wrapping key.
def hybrid_wrap_fek(sender_xpriv: x25519.X25519PrivateKey, receiver_xpub_bytes: bytes, fek: bytes):
    # X25519 shared secret
    receiver_xpub = x25519.X25519PublicKey.from_public_bytes(receiver_xpub_bytes)
    shared = sender_xpriv.exchange(receiver_xpub)

    # Mock PQC contribution: for demo we simulate an additional PQC shared secret.
    # In production replace this with e.g., Kyber KEM output.
    pqc_shared = hashlib.blake2s(shared + b'pqcdemo', digest_size=32).digest()

    # combine both secrets using HKDF
    wrap_key = hkdf_derive(shared + pqc_shared, info=b"suraksh-fek-wrap", length=32)

    # encrypt FEK with AESGCM using derived wrap_key
    wrapped = aesgcm_encrypt(wrap_key, fek, associated_data=b"fek-wrap")
    return wrapped, wrap_key  # returning wrap_key for testing/demo (do NOT expose in prod)

def hybrid_unwrap_fek(receiver_xpriv: x25519.X25519PrivateKey, sender_xpub_bytes: bytes, wrapped_blob: bytes):
    sender_xpub = x25519.X25519PublicKey.from_public_bytes(sender_xpub_bytes)
    shared = receiver_xpriv.exchange(sender_xpub)
    pqc_shared = hashlib.blake2s(shared + b'pqcdemo', digest_size=32).digest()
    wrap_key = hkdf_derive(shared + pqc_shared, info=b"suraksh-fek-wrap", length=32)
    fek = aesgcm_decrypt(wrap_key, wrapped_blob, associated_data=b"fek-wrap")
    return fek

# Bit-permutation (complex but deterministic and reversible)
def bits_from_bytes(b: bytes) -> bitarray:
    ba = bitarray(endian='big')
    ba.frombytes(b)
    return ba

def bytes_from_bits(ba: bitarray) -> bytes:
    return ba.tobytes()

def bit_permutation_obfuscate(data: bytes, seed: bytes) -> bytes:
    """
    Deterministic, reversible bit-level permutation.
    Security: Obfuscates file structure at bit level before encryption.
    seed: bytes (e.g., derived from FEK) used to seed the PRNG.
    """
    ba = bits_from_bytes(data)
    n = len(ba)
    if n == 0:
        return b''

    # Create pseudo-random sequence of swaps derived from seed
    rnd = hashlib.blake2b(seed, digest_size=64).digest()
    # expand to indices using iterative hashing
    swaps = []
    cursor = rnd
    needed = min(n // 2, 1000)  # limit swaps to reasonable number; more swaps => more complex
    i = 0
    while len(swaps) < needed:
        cursor = hashlib.blake2b(cursor + i.to_bytes(4, 'big'), digest_size=64).digest()
        for j in range(0, 64, 4):
            a = int.from_bytes(cursor[j:j+2], 'big') % n
            b = int.from_bytes(cursor[j+2:j+4], 'big') % n
            if a != b:
                swaps.append((a, b))
                if len(swaps) >= needed:
                    break
        i += 1

    # Apply swaps
    for a, b in swaps:
        ba[a], ba[b] = ba[b], ba[a]

    return bytes_from_bits(ba)

def bit_permutation_reverse(obf: bytes, seed: bytes) -> bytes:
    """
    Reverse bit-level permutation to restore original file structure.
    Security: Deterministic reversal using same FEK-derived seed.
    """
    ba = bits_from_bytes(obf)
    n = len(ba)
    if n == 0:
        return b''
    rnd = hashlib.blake2b(seed, digest_size=64).digest()
    swaps = []
    cursor = rnd
    needed = min(n // 2, 1000)
    i = 0
    while len(swaps) < needed:
        cursor = hashlib.blake2b(cursor + i.to_bytes(4, 'big'), digest_size=64).digest()
        for j in range(0, 64, 4):
            a = int.from_bytes(cursor[j:j+2], 'big') % n
            b = int.from_bytes(cursor[j+2:j+4], 'big') % n
            if a != b:
                swaps.append((a, b))
                if len(swaps) >= needed:
                    break
        i += 1
    # reverse swaps
    for a, b in reversed(swaps):
        ba[a], ba[b] = ba[b], ba[a]
    return bytes_from_bits(ba)

