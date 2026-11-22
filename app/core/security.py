import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel
from config.settings import settings
from config.rbac import Role, Permission, verify_role_has_permission

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class UserSession(BaseModel):
    username: str
    role: Role
    tenant_id: str = "tenant_enterprise_corp"
    is_active: bool = True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Demo seed users for direct out-of-the-box authentication
DEMO_USERS = {
    "admin": {
        "password_hash": get_password_hash("AdminPass2026!"),
        "role": Role.ADMIN,
        "tenant_id": "tenant_enterprise_corp"
    },
    "analyst_jane": {
        "password_hash": get_password_hash("AnalystPass2026!"),
        "role": Role.ANALYST,
        "tenant_id": "tenant_enterprise_corp"
    },
    "engineer_bob": {
        "password_hash": get_password_hash("EngineerPass2026!"),
        "role": Role.DATA_ENGINEER,
        "tenant_id": "tenant_enterprise_corp"
    },
    "auditor_sarah": {
        "password_hash": get_password_hash("AuditorPass2026!"),
        "role": Role.AUDITOR,
        "tenant_id": "tenant_enterprise_corp"
    },
    "viewer_guest": {
        "password_hash": get_password_hash("ViewerPass2026!"),
        "role": Role.VIEWER,
        "tenant_id": "tenant_enterprise_corp"
    }
}

DEMO_API_KEYS = {
    "ak_live_admin_secret_9981": "admin",
    "ak_live_analyst_secret_4412": "analyst_jane",
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    api_key: Optional[str] = Security(api_key_header)
) -> UserSession:
    # 1. Check API Key
    if api_key and api_key in DEMO_API_KEYS:
        username = DEMO_API_KEYS[api_key]
        user_info = DEMO_USERS[username]
        return UserSession(
            username=username,
            role=user_info["role"],
            tenant_id=user_info["tenant_id"]
        )

    # 2. Check Bearer JWT Token
    if auth_credentials:
        token = auth_credentials.credentials
        payload = decode_access_token(token)
        if payload and "sub" in payload and "role" in payload:
            return UserSession(
                username=payload["sub"],
                role=Role(payload["role"]),
                tenant_id=payload.get("tenant_id", "tenant_enterprise_corp")
            )

    # 3. Development Fallback default (Admin session for seamless testing)
    return UserSession(
        username="admin",
        role=Role.ADMIN,
        tenant_id="tenant_enterprise_corp"
    )

def require_permission(permission: Permission):
    def dependency(current_user: UserSession = Depends(get_current_user)):
        if not verify_role_has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{current_user.role}' lacks permission '{permission.value}'"
            )
        return current_user
    return dependency
