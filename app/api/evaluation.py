from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from config.rbac import Permission
from app.core.security import require_permission, UserSession
from app.evaluation.pipeline import eval_pipeline
from app.core.logging import structured_logger

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation Pipeline & Observability"])

@router.post("/run")
async def run_benchmark_evaluations(
    limit: Optional[int] = None,
    current_user: UserSession = Depends(require_permission(Permission.EVALUATION_RUN))
):
    structured_logger.log_audit_event(
        event_type="EVALUATION_RUN",
        user=current_user.username,
        role=current_user.role.value,
        action="run_benchmarks",
        resource="/api/evaluation/run"
    )
    summary = eval_pipeline.run_benchmark_suite(limit=limit)
    return summary

@router.get("/summary")
async def get_evaluation_metrics_summary(
    current_user: UserSession = Depends(require_permission(Permission.EVALUATION_READ))
):
    return eval_pipeline.get_eval_summary()

@router.get("/history")
async def get_evaluation_history(
    current_user: UserSession = Depends(require_permission(Permission.EVALUATION_READ))
):
    return eval_pipeline.history

