from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.rbac import Permission
from app.core.security import require_permission, UserSession
from app.agents.crew import crew_engine
from app.agents.planner import planner_agent
from app.core.telemetry import telemetry

router = APIRouter(prefix="/api/workflows", tags=["CrewAI Multi-Agent Workflows"])

class WorkflowExecuteRequest(BaseModel):
    query: str
    session_id: Optional[str] = "session_user"

class PlanRequest(BaseModel):
    query: str

@router.post("/execute")
async def execute_multi_agent_workflow(
    payload: WorkflowExecuteRequest,
    current_user: UserSession = Depends(require_permission(Permission.WORKFLOW_EXECUTE))
):
    result = crew_engine.execute_workflow(
        query=payload.query,
        user=current_user.username,
        role=current_user.role.value,
        session_id=payload.session_id or "session_default"
    )
    return result

@router.post("/plan")
async def generate_workflow_plan(
    payload: PlanRequest,
    current_user: UserSession = Depends(require_permission(Permission.WORKFLOW_PLAN))
):
    plan = planner_agent.plan(user_query=payload.query)
    return plan.dict()

@router.get("/traces")
async def get_execution_traces(
    limit: int = 15,
    current_user: UserSession = Depends(require_permission(Permission.WORKFLOW_READ))
):
    traces = telemetry.get_recent_traces(limit=limit)
    return [t.dict() for t in traces]

@router.get("/traces/{trace_id}")
async def get_trace_by_id(
    trace_id: str,
    current_user: UserSession = Depends(require_permission(Permission.WORKFLOW_READ))
):
    if trace_id not in telemetry.traces:
        raise HTTPException(status_code=404, detail="Trace not found")
    return telemetry.traces[trace_id].dict()

