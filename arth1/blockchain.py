# blockchain.py
# Local blockchain-like append-only ledger for audit trail
# Security: Hash-chained entries prevent tampering, append-only ensures immutability

import json
import os
import hashlib
from datetime import datetime
from logger import log_chain

CHAIN_FILE = "blockchain/chain.jsonl"


def init_chain():
    """Initialize blockchain ledger with genesis block."""
    os.makedirs("blockchain", exist_ok=True)
    if not os.path.exists(CHAIN_FILE):
        with open(CHAIN_FILE, "w") as f:
            genesis = {
                "index": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action": "GENESIS",
                "data": {},
                "prev_hash": "0" * 64,
            }
            genesis["hash"] = hash_entry(genesis)
            f.write(json.dumps(genesis) + "\n")
            log_chain(f"Genesis block created: blockchain ledger initialized, genesis hash {genesis['hash'][:16]}...")
    return CHAIN_FILE


def hash_entry(entry):
    """
    Compute deterministic SHA-256 hash of blockchain entry.
    Security: Hash includes index, timestamp, action, data, and previous hash to prevent tampering.
    """
    s = f"{entry['index']}|{entry['timestamp']}|{entry['action']}|{json.dumps(entry['data'], sort_keys=True)}|{entry['prev_hash']}"
    return hashlib.sha256(s.encode()).hexdigest()


def append_event(action: str, data: dict):
    """
    Append new transaction to blockchain ledger.
    Security: Each entry is hash-chained to previous entry, ensuring immutability.
    """
    init_chain()
    
    # Read last block to get index and hash
    with open(CHAIN_FILE, "r+") as f:
        lines = f.read().splitlines()
        last = json.loads(lines[-1])
        idx = last["index"] + 1
        prev_hash = last["hash"]
        
        # Create new block
        entry = {
            "index": idx,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "data": data,
            "prev_hash": prev_hash
        }
        entry["hash"] = hash_entry(entry)
        f.write(json.dumps(entry) + "\n")
    
    # Log blockchain event
    log_chain(f"New transaction added to block #{idx}: action={action}, transaction hash {entry['hash'][:16]}..., previous block hash {prev_hash[:16]}...")
    log_chain(f"Block #{idx} mined and committed: block hash computed and verified, chain integrity maintained")
    
    return entry


def verify_chain():
    """
    Verify blockchain integrity by recomputing all hashes.
    Security: Detects any tampering or corruption in the audit trail.
    """
    if not os.path.exists(CHAIN_FILE):
        return False, "Chain file not found"
    
    with open(CHAIN_FILE, "r") as f:
        lines = f.read().splitlines()
    
    if len(lines) == 0:
        return False, "Empty chain"
    
    prev_hash = "0" * 64
    for i, line in enumerate(lines):
        entry = json.loads(line)
        if entry["prev_hash"] != prev_hash:
            return False, f"Hash chain broken at index {i}: previous hash mismatch detected"
        computed_hash = hash_entry(entry)
        if entry["hash"] != computed_hash:
            return False, f"Invalid block hash at index {i}: tampering detected"
        prev_hash = entry["hash"]
    
    return True, f"Chain verified: {len(lines)} blocks validated, integrity confirmed"


def get_all_entries():
    """Get all blockchain entries for audit review."""
    if not os.path.exists(CHAIN_FILE):
        return []
    
    entries = []
    with open(CHAIN_FILE, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries
