from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
from backend.app.core.config import settings

security = HTTPBearer(auto_error=False)

class UserPayload(BaseModel):
    user_id: str
    org_id: str
    role: str  # 'creator' | 'reviewer' | 'manager' | 'admin'
    email: str = ""
    full_name: str = ""

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Predefined demo accounts for easy role switching (Team Double Trouble / Lumina Skincare)
DEMO_USERS = {
    "creator": {
        "user_id": "00000000-0000-0000-0000-000000000101",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "role": "creator",
        "email": "creator@luminaskincare.com",
        "full_name": "Elena Vance (Creator)",
    },
    "reviewer": {
        "user_id": "00000000-0000-0000-0000-000000000102",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "role": "reviewer",
        "email": "reviewer@luminaskincare.com",
        "full_name": "Marcus Brody (Reviewer)",
    },
    "manager": {
        "user_id": "00000000-0000-0000-0000-000000000103",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "role": "manager",
        "email": "sarah@luminaskincare.com",
        "full_name": "Sarah Chen (Manager)",
    },
    "admin": {
        "user_id": "00000000-0000-0000-0000-000000000104",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "role": "admin",
        "email": "admin@luminaskincare.com",
        "full_name": "Devin Archer (Admin)",
    },
}

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> UserPayload:
    """
    Retrieves current user. Supports Bearer token or quick-switch X-User-Role header for rapid hackathon grading/switching.
    """
    if x_user_role and x_user_role.lower() in DEMO_USERS:
        return UserPayload(**DEMO_USERS[x_user_role.lower()])

    if credentials:
        payload = decode_token(credentials.credentials)
        return UserPayload(
            user_id=payload.get("user_id", payload.get("sub", "")),
            org_id=payload.get("org_id", "00000000-0000-0000-0000-000000000001"),
            role=payload.get("role", "creator"),
            email=payload.get("email", ""),
            full_name=payload.get("full_name", ""),
        )

    # Default fallback to Creator for frictionless testing
    return UserPayload(**DEMO_USERS["creator"])

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: UserPayload = Depends(get_current_user)) -> UserPayload:
        if current_user.role.lower() not in [r.lower() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{current_user.role}' is not in allowed roles {allowed_roles}",
            )
        return current_user
    return role_checker
