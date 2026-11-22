from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from config.settings import settings
from config.rbac import Role, ROLE_PERMISSIONS
from app.core.security import (
    DEMO_USERS,
    verify_password,
    create_access_token,
    get_current_user,
    UserSession
)
from app.core.logging import structured_logger

router = APIRouter(prefix="/api/auth", tags=["Authentication & RBAC"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class UserProfile(BaseModel):
    username: str
    role: str
    tenant_id: str
    permissions: list[str]

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_record = DEMO_USERS.get(form_data.username)
    if not user_record or not verify_password(form_data.password, user_record["password_hash"]):
        structured_logger.log_audit_event(
            event_type="AUTH_FAILURE",
            user=form_data.username,
            role="anonymous",
            action="login",
            resource="/api/auth/token",
            status="FAILED"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": form_data.username, "role": user_record["role"].value, "tenant_id": user_record["tenant_id"]}
    )

    structured_logger.log_audit_event(
        event_type="AUTH_SUCCESS",
        user=form_data.username,
        role=user_record["role"].value,
        action="login",
        resource="/api/auth/token",
        status="SUCCESS"
    )

    return TokenResponse(
        access_token=access_token,
        role=user_record["role"].value,
        username=form_data.username
    )

@router.get("/me", response_model=UserProfile)
async def read_users_me(current_user: UserSession = Depends(get_current_user)):
    perms = [p.value for p in ROLE_PERMISSIONS.get(current_user.role, set())]
    return UserProfile(
        username=current_user.username,
        role=current_user.role.value,
        tenant_id=current_user.tenant_id,
        permissions=perms
    )

