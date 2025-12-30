# users.py
# Simple user store for Phase-1 demo (Suraksh)
# Clearance: L1=lowest, L2=medium, L3=highest, 4=superuser

import os
import json
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization

USERS_FILE = "vault_storage/keys/users.json"


class User:
    def __init__(self, user_id, name, org, clearance, password="root"):
        self.user_id = user_id
        self.name = name
        self.org = org
        self.clearance = clearance  # 1 (lowest), 2 (medium), 3 (highest), 4 (superuser)
        self.password = password

        self.x25519_private = None
        self.x25519_public = None
        self.ed25519_private = None
        self.ed25519_public = None

    def to_public_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "org": self.org,
            "clearance": self.clearance,
            "x25519_public": self.x25519_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex(),
            "ed25519_public": self.ed25519_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex(),
        }


def init_users():
    """
    Create demo users with clearances 1 (lowest), 2 (medium), 3 (highest), 4 (superuser).
    If users.json already exists, it is reused (keys are preserved).
    Ensures SU superuser always exists.
    """
    os.makedirs("vault_storage/keys", exist_ok=True)

    users = [
        ("U1", "FieldOfficer", "Police", 1),  # L1 = lowest
        ("U2", "SeniorOfficer", "Police", 2),  # L2 = medium
        ("U3", "Chief", "Police", 3),         # L3 = highest
        ("SU", "SuperUser", "Admin", 4),      # Superuser
    ]

    # If file exists, load and ensure all users exist (especially SU)
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            store = json.load(f)
    else:
        store = {}

    # Ensure all users exist, generate keys for missing ones
    for uid, name, org, cl in users:
        if uid not in store:
            # Generate long-term keys
            xpriv = x25519.X25519PrivateKey.generate()
            xpub = xpriv.public_key()

            epriv = ed25519.Ed25519PrivateKey.generate()
            epub = epriv.public_key()

            store[uid] = {
                "user_id": uid,
                "name": name,
                "org": org,
                "clearance": cl,
                "password": "root",  # demo only

                # X25519 (key exchange)
                "x25519_private": xpriv.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                ).hex(),

                "x25519_public": xpub.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                ).hex(),

                # Ed25519 (signing)
                "ed25519_private": epriv.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                ).hex(),

                "ed25519_public": epub.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                ).hex(),
            }
        else:
            # Ensure password is set correctly (case-sensitive)
            if "password" not in store[uid] or store[uid]["password"] != "root":
                store[uid]["password"] = "root"

    with open(USERS_FILE, "w") as f:
        json.dump(store, f, indent=2)

    return store


def load_user(user_id):
    """
    Load a user record by user_id.
    """
    if not os.path.exists(USERS_FILE):
        return None

    with open(USERS_FILE, "r") as f:
        store = json.load(f)

    return store.get(user_id)


def is_superuser(user_id):
    """Check if user is superuser (clearance 4)."""
    u = load_user(user_id)
    return u and u.get("clearance") == 4
