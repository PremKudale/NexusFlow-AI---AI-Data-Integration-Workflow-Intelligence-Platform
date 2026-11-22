from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from config.rbac import Permission
from app.core.security import require_permission, UserSession
from app.core.logging import structured_logger
from app.event_driven.retry_manager import dlq

router = APIRouter(prefix="/api/audit", tags=["Audit Trail & Reliability"])

@router.get("/logs")
async def get_audit_logs(
    limit: int = 50,
    current_user: UserSession = Depends(require_permission(Permission.AUDIT_READ))
):
    logs = structured_logger.get_recent_audit_logs(limit=limit)
    return {
        "count": len(logs),
        "tamper_evident": True,
        "logs": logs
    }

@router.get("/dlq")
async def get_dead_letter_queue(
    current_user: UserSession = Depends(require_permission(Permission.AUDIT_READ))
):
    messages = dlq.get_messages()
    return {
        "dlq_count": len(messages),
        "messages": messages
    }

