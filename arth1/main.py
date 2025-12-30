# main.py
# Quick CLI demo and vault initialization. Also creates sample upload file.
import os
from users import init_users, load_user
from vault import init_vault, upload_file, retrieve_file, share_file
from blockchain import init_chain
import shutil

def create_sample():
    os.makedirs("sample_uploads", exist_ok=True)
    with open("sample_uploads/sample-evidence.txt", "w") as f:
        f.write("CONFIDENTIAL CASE FILE: OPERATION SURAKSH\nSensitive intelligence content for demo.\n")

def cli_demo():
    print("Initializing users, vault, chain...")
    init_users()
    init_vault()
    init_chain()
    create_sample()
    from users import load_user
    chief = load_user("U1")
    field = load_user("U3")

    print("\nUploading sample file as Chief (L1):")
    fid = upload_file(chief, "sample_uploads/sample-evidence.txt", clearance=1)
    print("Uploaded File ID:", fid)

    print("\nChief retrieves file (should succeed):")
    data = retrieve_file(chief, fid)
    print(data.decode()[:200])

    print("\nField officer tries to retrieve (should be ACCESS DENIED):")
    print(retrieve_file(field, fid))

if __name__ == "__main__":
    cli_demo()
    print("\nStart Flask UI: python app.py")

