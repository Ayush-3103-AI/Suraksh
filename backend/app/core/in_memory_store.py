"""
In-Memory Storage for Phase 1
Temporary storage for users.
Will be replaced with database in Phase 2.
"""

from typing import Dict, Optional

# Import User for type hints (circular import is avoided by lazy import in security.py)
from app.core.security import User


def _init_default_users() -> Dict[str, dict]:
    """
    Initialize default users with hashed passwords.
    All default users have password: "test"
    """
    # Fixed: Use pre-computed bcrypt hash to avoid passlib/bcrypt compatibility issues
    # This hash corresponds to password "test" generated with bcrypt
    hashed_password = "$2b$12$GGQR5DvvsJIRNxDRUGoRiuiWKXhxtLTt.5BAcNSmbvWMY7ETv9nIG"
    
    return {
        "test": {
            "username": "test",
            "email": "test@suraksh.local",
            "hashed_password": hashed_password,
            "clearance_level": "L1",
            "is_active": True,
        },
        "admin": {
            "username": "admin",
            "email": "admin@suraksh.local",
            "hashed_password": hashed_password,
            "clearance_level": "L3",
            "is_active": True,
        },
        "analyst": {
            "username": "analyst",
            "email": "analyst@suraksh.local",
            "hashed_password": hashed_password,
            "clearance_level": "L2",
            "is_active": True,
        },
    }


# In-memory user store
# Fixed: Initialize lazily to avoid import-time bcrypt errors
_users: Optional[Dict[str, dict]] = None

def _get_users() -> Dict[str, dict]:
    """Lazy initialization of users."""
    global _users
    if _users is None:
        _users = _init_default_users()
    return _users


def get_user_by_username(username: str) -> Optional[User]:
    """
    Get user by username from in-memory store.
    
    Args:
        username: Username to lookup
        
    Returns:
        User object if found, None otherwise
    """
    users = _get_users()
    user_data = users.get(username)
    if user_data:
        return User(
            username=user_data["username"],
            email=user_data["email"],
            clearance_level=user_data["clearance_level"],
            is_active=user_data["is_active"],
        )
    return None


def get_user_with_password(username: str) -> Optional[dict]:
    """
    Get user with password hash for authentication.
    
    Args:
        username: Username to lookup
        
    Returns:
        User dict with password hash if found, None otherwise
    """
    users = _get_users()
    return users.get(username)


def create_user(
    username: str,
    email: str,
    hashed_password: str,
    clearance_level: str,
) -> User:
    """
    Create a new user in in-memory store.
    
    Args:
        username: Username
        email: Email address
        hashed_password: Hashed password
        clearance_level: Clearance level (L1, L2, L3)
        
    Returns:
        Created User object
    """
    users = _get_users()
    users[username] = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "clearance_level": clearance_level,
        "is_active": True,
    }
    
    return User(
        username=username,
        email=email,
        clearance_level=clearance_level,
        is_active=True,
    )



