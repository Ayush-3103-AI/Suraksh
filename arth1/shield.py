# shield.py
# Shield Engine: validates user identity & clearance for requests
# Clearance model: L1=lowest, L2=medium, L3=highest, 4=superuser
# Higher clearance users CAN view lower clearance files
# Lower clearance users CANNOT view higher clearance files

from users import load_user, is_superuser
from logger import log_app
import json


def get_user_public_profile(user_id):
    """Return minimal profile from persisted users."""
    u = load_user(user_id)
    if not u:
        return None
    return {
        "user_id": u["user_id"],
        "name": u["name"],
        "clearance": u["clearance"],
        "x25519_public": bytes.fromhex(u["x25519_public"]) if "x25519_public" in u else None,
        "ed25519_public": bytes.fromhex(u["ed25519_public"]) if "ed25519_public" in u else None
    }


def authenticate(user_id, password):
    """Authenticate user and return user info. Case-sensitive user_id and password matching."""
    # Case-sensitive user_id lookup
    u = load_user(user_id)
    if not u:
        log_app(f"Authentication failed: user {user_id} not found in system")
        return None
    
    # Case-sensitive password comparison
    stored_password = u.get("password", "")
    if password != stored_password:
        log_app(f"Authentication failed: user {user_id} invalid password")
        return None
    
    clearance_level = u["clearance"]
    clearance_name = {1: "L1 (Lowest)", 2: "L2 (Medium)", 3: "L3 (Highest)", 4: "L4 (Superuser)"}.get(clearance_level, "Unknown")
    
    # Special log for superuser
    if clearance_level == 4:
        log_app(f"[AUTH] Superuser authenticated successfully: user {user_id} ({u['name']}) authenticated with clearance {clearance_name}")
    else:
        log_app(f"Authentication successful: user {user_id} ({u['name']}) authenticated with clearance {clearance_name}")
    
    return {
        "user_id": u["user_id"],
        "name": u["name"],
        "clearance": u["clearance"],
        "x25519_private": bytes.fromhex(u["x25519_private"]),
        "x25519_public": bytes.fromhex(u["x25519_public"])
    }


def validate_access(user_id: str, file_clearance: int, approved_access: list = None):
    """
    Validate if user can access file based on clearance hierarchy.
    
    Clearance hierarchy: L1 (lowest) < L2 (medium) < L3 (highest) < L4 (superuser)
    Rule: Higher clearance users CAN view lower clearance files.
          Lower clearance users CANNOT view higher clearance files.
    
    Returns: (allowed: bool, reason: str)
    """
    user = load_user(user_id)
    if not user:
        log_app(f"Access validation failed: user {user_id} not found")
        return False, "USER NOT FOUND"
    
    user_clearance = user["clearance"]
    file_clearance_name = {1: "L1", 2: "L2", 3: "L3"}.get(file_clearance, f"L{file_clearance}")
    user_clearance_name = {1: "L1", 2: "L2", 3: "L3", 4: "L4"}.get(user_clearance, f"L{user_clearance}")
    
    # Superuser can access everything
    if user_clearance == 4:
        log_app(f"Access granted: superuser {user_id} authorized to access {file_clearance_name} file")
        return True, "SUPERUSER"
    
    # Higher clearance users can view lower clearance files
    # user_clearance > file_clearance means user has higher clearance (e.g., L3 > L1)
    if user_clearance > file_clearance:
        log_app(f"Access granted: user {user_id} ({user_clearance_name}) has sufficient clearance to access {file_clearance_name} file")
        return True, "CLEARANCE_SUFFICIENT"
    
    # Equal clearance: user can access their own clearance level
    if user_clearance == file_clearance:
        log_app(f"Access granted: user {user_id} ({user_clearance_name}) authorized to access file at same clearance level")
        return True, "CLEARANCE_MATCH"
    
    # Lower clearance: check approved access
    if approved_access and user_id in approved_access:
        log_app(f"Access granted: user {user_id} ({user_clearance_name}) authorized via approved access request for {file_clearance_name} file")
        return True, "APPROVED_ACCESS"
    
    # Access denied: user clearance insufficient
    log_app(f"Access denied: user {user_id} ({user_clearance_name}) lacks sufficient clearance to access {file_clearance_name} file. Request access required.")
    return False, "ACCESS_DENIED"


def can_view_file(user_id: str, file_clearance: int):
    """
    Determine if user can VIEW (not necessarily access) a file.
    Higher clearance users can VIEW lower clearance files.
    Lower clearance users cannot VIEW higher clearance files.
    """
    user = load_user(user_id)
    if not user:
        return False
    
    user_clearance = user["clearance"]
    
    # Superuser can view everything
    if user_clearance == 4:
        return True
    
    # Higher clearance users can view lower clearance files
    # user_clearance > file_clearance means user has higher clearance
    if user_clearance >= file_clearance:
        return True
    
    return False
