from enum import Enum
from typing import List, Set
from fastapi import HTTPException, status

class Role(str, Enum):
    ADMIN = "admin"
    DATA_ENGINEER = "data_engineer"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    VIEWER = "viewer"

class Permission(str, Enum):
    # Ingestion permissions
    DATA_INGEST = "data:ingest"
    DATA_DELETE = "data:delete"
    DATA_READ = "data:read"

    # Agent & Workflow permissions
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_PLAN = "workflow:plan"
    WORKFLOW_READ = "workflow:read"

    # Evaluation permissions
    EVALUATION_RUN = "evaluation:run"
    EVALUATION_READ = "evaluation:read"

    # Audit & Security permissions
    AUDIT_READ = "audit:read"
    SYSTEM_CONFIG = "system:config"

ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.DATA_ENGINEER: {
        Permission.DATA_INGEST,
        Permission.DATA_DELETE,
        Permission.DATA_READ,
        Permission.WORKFLOW_READ,
        Permission.EVALUATION_RUN,
        Permission.EVALUATION_READ,
    },
    Role.ANALYST: {
        Permission.DATA_READ,
        Permission.WORKFLOW_EXECUTE,
        Permission.WORKFLOW_PLAN,
        Permission.WORKFLOW_READ,
        Permission.EVALUATION_RUN,
        Permission.EVALUATION_READ,
    },
    Role.AUDITOR: {
        Permission.DATA_READ,
        Permission.WORKFLOW_READ,
        Permission.EVALUATION_READ,
        Permission.AUDIT_READ,
    },
    Role.VIEWER: {
        Permission.DATA_READ,
        Permission.WORKFLOW_READ,
        Permission.EVALUATION_READ,
    },
}

def verify_role_has_permission(role: Role, required_permission: Permission) -> bool:
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return required_permission in role_perms

