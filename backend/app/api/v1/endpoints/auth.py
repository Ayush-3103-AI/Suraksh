"""
Authentication Endpoints
Login, registration, and user info endpoints with JWT and PQC support.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.in_memory_store import (
    create_user,
    get_user_with_password,
)
from app.core.security import (
    Token,
    User,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)

router = APIRouter()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """User registration request model."""
    username: str
    email: EmailStr
    password: str
    clearance_level: str = "L1"  # Default to L1, can be overridden


class UserResponse(BaseModel):
    """User response model."""
    username: str
    email: str
    clearance_level: str
    is_active: bool


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest) -> Token:
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: Login credentials (username and password)
        
    Returns:
        JWT token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # #region agent log
    import json
    try:
        with open(r'd:\Hacakathons\Suraksh\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"location":"auth.py:51","message":"Login endpoint called","data":{"username":credentials.username},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    user_data = get_user_with_password(credentials.username)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(credentials.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # Create JWT token
    access_token_expires = None  # Use default from settings
    token_data = {
        "sub": user_data["username"],
        "clearance_level": user_data["clearance_level"],
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest) -> UserResponse:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If username already exists or invalid clearance level
    """
    # Validate clearance level
    if user_data.clearance_level not in ["L1", "L2", "L3"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid clearance level. Must be L1, L2, or L3"
        )
    
    # Check if user already exists
    existing_user = get_user_with_password(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user = create_user(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        clearance_level=user_data.clearance_level,
    )
    
    return UserResponse(
        username=user.username,
        email=user.email,
        clearance_level=user.clearance_level,
        is_active=user.is_active,
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = get_current_active_user,
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        Current user information
    """
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        clearance_level=current_user.clearance_level,
        is_active=current_user.is_active,
    )

