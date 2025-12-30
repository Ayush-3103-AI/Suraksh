# Suraksh Phase-1 - Secure Vault System

## Overview
Suraksh is a defense-grade secure vault system implementing:
- Multi-level clearance-based access control (L1=Lowest, L2=Medium, L3=Highest, L4=Superuser)
- End-to-end file encryption with bit permutation obfuscation
- Hybrid key wrapping (X25519 + PQC placeholder)
- Request-approval workflow for cross-clearance access
- Local blockchain-like append-only audit ledger
- Re-encryption on file sharing (new FEK per share)

## Project Structure
```
suraksh_phase1/
├── app.py                 # Single entry point (Flask UI)
├── users.py               # User management & key generation
├── crypto.py              # Cryptographic primitives
├── vault.py               # Vault storage operations
├── shield.py              # Access control engine
├── blockchain.py          # Local blockchain ledger
├── logger.py              # Structured logging
├── requirements.txt       # Python dependencies
├── templates/            # Flask HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── request.html
│   ├── share.html
│   ├── approve.html
│   └── blockchain.html
└── vault_storage/        # Created on first run
    ├── files/           # Encrypted chunks
    ├── keys/            # User keys & clearance keys
    ├── metadata/        # Per-file metadata JSON
    └── temp/            # Intermediate files
└── blockchain/          # Created on first run
    └── chain.jsonl     # Append-only ledger
```

## Installation & Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

The application will:
- Initialize users (U1=FieldOfficer L1, U2=SeniorOfficer L2, U3=Chief L3, SU=SuperUser L4)
- Create vault directories
- Initialize blockchain ledger
- Start Flask server at http://127.0.0.1:5000

## Usage

### Login
- **URL:** http://127.0.0.1:5000
- **Password for all users:** `root`
- **Users:**
  - U1 - FieldOfficer (L1 - Lowest clearance)
  - U2 - SeniorOfficer (L2 - Medium clearance)
  - U3 - Chief (L3 - Highest clearance)
  - SU - SuperUser (L4 - Can access all files)

### Features

#### 1. File Upload
- Navigate to "Upload File"
- Select file and clearance level (L1/L2/L3)
- File processing:
  - Binary conversion
  - Bit permutation obfuscation
  - Chunking (4KB chunks)
  - AES-256-GCM encryption per chunk
  - FEK wrapped with clearance key
  - Stored in vault

#### 2. File Access
- Users see files ≤ their clearance level
- Higher-clearance files visible but marked "Access Denied"
- Click "Request Access" to request higher-clearance files
- Superuser can access all files

#### 3. Request-Access Workflow
- Lower-clearance user requests access to higher-clearance file
- Request logged in blockchain
- Superuser sees pending requests in "Approve Requests"
- Superuser can approve/deny
- Approved users added to file's approved_access list

#### 4. File Sharing
- Sender must have access to file
- Receiver must have equal or higher clearance
- File is **re-encrypted** with NEW FEK
- New file ID created
- Share event logged

#### 5. Blockchain Viewer
- View all blockchain entries
- Verify chain integrity
- See all actions: UPLOAD, ACCESS, SHARE, REQUEST, APPROVE, DENY

## Logging

### Terminal A (stdout) - Blockchain Events
Shows real-time blockchain events:
```
[BLOCKCHAIN] 15:30:45 | ACTION: UPLOAD | DATA: {'file_id': 'abc123...', 'uploader': 'U1', ...}
[BLOCKCHAIN] 15:30:50 | ACTION: REQUEST | DATA: {'request_id': 'def456...', ...}
```

### Terminal B (stderr) - Crypto Pipeline
Shows cryptographic operations:
```
[CRYPTO] 15:30:45 | UPLOAD_START File: evidence.txt, Clearance: L3
[CRYPTO] 15:30:45 | BINARY_CONVERSION File size: 1024 bytes
[CRYPTO] 15:30:45 | FEK_GENERATED 256-bit key: a1b2c3d4...
[CRYPTO] 15:30:45 | BIT_PERMUTATION_START Input size: 1024 bytes
[CRYPTO] 15:30:45 | BIT_PERMUTATION_COMPLETE Applied 500 swaps
[CRYPTO] 15:30:45 | CHUNKING_START Total chunks: 1, Chunk size: 4096
[CRYPTO] 15:30:45 | CHUNK_ENCRYPTED Chunk 1/1: 4120 bytes
[CRYPTO] 15:30:45 | ENCRYPTION_COMPLETE All 1 chunks encrypted
[CRYPTO] 15:30:45 | FEK_WRAPPED FEK wrapped with L3 clearance key
[CRYPTO] 15:30:45 | UPLOAD_COMPLETE File ID: abc123...
```

## Security Notes

### Production Considerations
1. **PQC Placeholder:** The hybrid wrapping uses a Blake2s-derived mock PQC contribution. Replace with actual Kyber KEM in production.
2. **HSM Integration:** Clearance keys should be stored in Hardware Security Modules, not files.
3. **Password Storage:** Current demo uses plaintext passwords. Use proper password hashing (bcrypt/argon2) in production.
4. **Session Security:** Change `app.secret_key` to a secure random value.
5. **Network Security:** Add TLS/HTTPS for production deployment.

### Clearance Model
- **L1 (Lowest):** Field officers, basic access
- **L2 (Medium):** Senior officers, medium sensitivity
- **L3 (Highest):** Chiefs, highest sensitivity
- **L4 (Superuser):** Admin, can access all files and approve requests

## Testing Workflow

1. **Login as U1 (L1 - Lowest)**
   - Upload a file with L3 clearance
   - Try to download it → Should be denied
   - Request access with reason
   
2. **Login as SU (Superuser)**
   - Go to "Approve Requests"
   - Approve U1's request
   
3. **Login as U1 again**
   - Should now be able to download the L3 file
   
4. **Share Test**
   - Login as U3 (L3)
   - Upload L3 file
   - Share with U2 (L2) → Should be denied (receiver clearance too low)
   - Share with SU (L4) → Should succeed, new file ID created

## Troubleshooting

### Port Already in Use
Change port in `app.py`:
```python
app.run(debug=True, host="127.0.0.1", port=5001)
```

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Clear All Data
Delete directories:
- `vault_storage/`
- `blockchain/`

Then restart the application.

## License
Defense Hackathon Project - Phase 1 Demo
