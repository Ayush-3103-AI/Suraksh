# app.py
# Single entry point for Suraksh Phase-1
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, jsonify
from users import init_users, load_user, is_superuser
from vault import (
    init_vault, upload_file, retrieve_file, share_file,
    request_access, get_pending_requests, approve_request, deny_request,
    list_all_metadata, read_metadata, create_clsd, retrieve_clsd, list_clsd_metadata
)
from blockchain import get_all_entries, verify_chain
from shield import authenticate, validate_access, can_view_file
from logger import log_app
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = "super-secret-demo-key-suraksh-phase1"  # change in production

# Initialize on startup
print("Initializing Suraksh Phase-1...")
init_users()
init_vault()
print("Initialization complete. Starting Flask server...")


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid = request.form["user_id"]
        pwd = request.form["password"]
        user = authenticate(uid, pwd)
        if user:
            session["user_id"] = uid
            session["name"] = user["name"]
            session["clearance"] = user["clearance"]
            log_app(f"User session established: {uid} logged in, session created")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials (demo password: root)")
    users = [
        ("U1", "FieldOfficer", "L1 (Lowest)"),
        ("U2", "SeniorOfficer", "L2 (Medium)"),
        ("U3", "Chief", "L3 (Highest)"),
        ("SU", "SuperUser", "L4 (Superuser)")
    ]
    return render_template("login.html", users=users)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    user_clearance = user["clearance"]
    
    # Get all files - separate normal files from CLSD documents
    all_files = list_all_metadata()
    
    # Process normal files with accessibility flags (existing logic)
    files_with_access = []
    
    for meta in all_files:
        # Skip CLSD documents - they are handled separately
        if meta.get("type") == "CLSD":
            continue
            
        file_clearance = meta["clearance"]
        
        # Check if user can ACCESS the file
        allowed, reason = validate_access(uid, file_clearance, meta.get("approved_access", []))
        
        # ALL files are visible, but accessibility determines color
        file_info = {
            **meta,
            "visible": True,
            "accessible": allowed
        }
        files_with_access.append(file_info)
    
    # Get CLSD documents visible to user (based on clearance)
    clsd_documents = list_clsd_metadata(user_clearance)
    
    # List bit-manipulated files for judges
    bit_files = list(Path("vault_storage/bit_manipulated").glob("*"))[:10] if Path("vault_storage/bit_manipulated").exists() else []
    
    return render_template("dashboard.html", 
                         user=user, 
                         files_with_access=files_with_access,
                         clsd_documents=clsd_documents,
                         bit_files=bit_files,
                         is_superuser=is_superuser(uid))


@app.route("/upload", methods=["GET"])
def upload():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    return render_template("upload.html")


@app.route("/upload-file", methods=["GET", "POST"])
def upload_file_route():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected")
            return redirect(url_for("upload_file_route"))
        
        f = request.files["file"]
        if f.filename == "":
            flash("No file selected")
            return redirect(url_for("upload_file_route"))
        
        level = int(request.form["clearance"])
        save_path = f"vault_storage/temp/upload_{f.filename}"
        f.save(save_path)
        
        fid = upload_file(user, save_path, clearance=level)
        flash(f"File uploaded successfully! File ID: {fid}")
        return redirect(url_for("dashboard"))
    
    return render_template("upload-file.html")


@app.route("/create-clsd", methods=["GET", "POST"])
def create_clsd_document():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        level1_content = request.form.get("level1_content", "").strip()
        level2_content = request.form.get("level2_content", "").strip()
        level3_content = request.form.get("level3_content", "").strip()
        
        if not title:
            flash("Title is required")
            return redirect(url_for("create_clsd_document"))
        
        if not level1_content and not level2_content and not level3_content:
            flash("At least one section must have content")
            return redirect(url_for("create_clsd_document"))
        
        document_id = create_clsd(user, title, level1_content, level2_content, level3_content)
        flash(f"Secure Document created successfully! Document ID: {document_id}")
        return redirect(url_for("dashboard"))
    
    return render_template("create-clsd.html")


@app.route("/view-clsd/<document_id>")
def view_clsd(document_id):
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    
    result, error = retrieve_clsd(user, document_id)
    
    if error:
        flash(error)
        return redirect(url_for("dashboard"))
    
    return render_template("view-clsd.html", document=result, user=user)


@app.route("/download/<file_id>")
def download(file_id):
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    res = retrieve_file(user, file_id)
    
    if isinstance(res, bytes):
        # Get metadata to retrieve original filename
        meta = read_metadata(file_id)
        if meta and "original_filename" in meta:
            original_filename = meta["original_filename"]
        else:
            # Fallback to stored filename or file_id
            original_filename = meta.get("filename", f"{file_id}.dec") if meta else f"{file_id}.dec"
        
        # Determine MIME type from extension
        import mimetypes
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        tmp = f"vault_storage/temp/{file_id}.out"
        with open(tmp, "wb") as tf:
            tf.write(res)
        return send_file(tmp, as_attachment=True, download_name=original_filename, mimetype=mime_type)
    else:
        flash(res)
        return redirect(url_for("dashboard"))


@app.route("/request/<file_id>", methods=["GET", "POST"])
def request_file_access(file_id):
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    meta = read_metadata(file_id)
    
    if not meta:
        flash("File not found")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        reason = request.form.get("reason", "")
        if not reason:
            flash("Please provide a reason")
            return redirect(url_for("request_file_access", file_id=file_id))
        
        req_id = request_access(uid, file_id, reason)
        flash(f"Access request submitted! Request ID: {req_id}")
        return redirect(url_for("dashboard"))
    
    return render_template("request.html", file_id=file_id, filename=meta.get("filename", "Unknown"))


@app.route("/share/<file_id>", methods=["GET", "POST"])
def share(file_id):
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    user = load_user(uid)
    meta = read_metadata(file_id)
    
    if not meta:
        flash("File not found")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        to = request.form["to_user"]
        target = load_user(to)
        if not target:
            flash("Target user not found")
            return redirect(url_for("share", file_id=file_id))
        
        new_id = share_file(user, target, file_id)
        if isinstance(new_id, str) and new_id.startswith("SHARE DENIED"):
            flash(new_id)
        else:
            flash(f"File shared successfully! New File ID: {new_id}")
        return redirect(url_for("dashboard"))
    
    users = [
        ("U1", "FieldOfficer", "L1"),
        ("U2", "SeniorOfficer", "L2"),
        ("U3", "Chief", "L3"),
        ("SU", "SuperUser", "L4")
    ]
    return render_template("share.html", file_id=file_id, users=users)


@app.route("/approve", methods=["GET", "POST"])
def approve():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    if not is_superuser(uid):
        flash("Access denied. Superuser only.")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        req_id = request.form.get("request_id")
        action = request.form.get("action")
        
        if action == "approve":
            result = approve_request(req_id, uid)
            flash(result)
        elif action == "deny":
            result = deny_request(req_id, uid)
            flash(result)
        
        return redirect(url_for("approve"))
    
    requests = get_pending_requests()
    
    for req in requests:
        meta = read_metadata(req["file_id"])
        req["file_meta"] = meta
    
    return render_template("approve.html", requests=requests)


@app.route("/blockchain")
def blockchain_viewer():
    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))
    
    entries = get_all_entries()
    is_valid, message = verify_chain()
    
    return render_template("blockchain.html", entries=entries, is_valid=is_valid, message=message)


if __name__ == "__main__":
    import sys
    import threading
    import time
    import random
    from logger import log_network
    
    # Disable Flask reloader for smooth execution flow
    # This prevents execution from appearing stuck
    use_reloader = "--reload" in sys.argv
    
    # Network-layer simulation: background thread emitting events every 30 seconds
    def network_simulation():
        """Background thread that simulates network intelligence events."""
        events = [
            "Speeding vehicle detected on NH-48",
            "Emergency 112 call transcript received",
            "Suspicious border movement flagged",
            "Live 112 call: \"Vehicle crash near junction 14\"",
            "Traffic violation detected: License plate ABC-1234",
            "Emergency response unit dispatched to Sector 7",
            "Anomaly detected in surveillance feed Zone-3",
            "High-priority alert: Unauthorized access attempt logged",
            "Real-time intelligence: Suspicious activity pattern identified",
            "Network alert: Multiple sensor triggers in proximity"
        ]
        
        time.sleep(5)  # Initial delay before first event
        
        while True:
            try:
                event = random.choice(events)
                log_network(f"ALERT | {event}")
                time.sleep(20)  # Emit event every 20 seconds
            except Exception:
                break
    
    # Start network simulation thread
    sim_thread = threading.Thread(target=network_simulation, daemon=True)
    sim_thread.start()
    
    print("\n" + "="*70)
    print("Suraksh Phase-1 - Secure Vault System")
    print("="*70)
    print("Flask UI: http://127.0.0.1:5000")
    print("\nLog Streams:")
    print("  [APPLICATION] - Authentication, clearance, access decisions (stdout)")
    print("  [BLOCKCHAIN]  - Transactions, blocks, audit trail (stdout + file)")
    print("  [NETWORK]     - Binary conversion, encryption, chunking (stderr)")
    print("="*70 + "\n")
    
    # Force flush to ensure startup message appears immediately
    sys.stdout.flush()
    sys.stderr.flush()
    
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=use_reloader)
