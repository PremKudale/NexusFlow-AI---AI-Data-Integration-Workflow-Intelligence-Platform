import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMouter = None
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config.settings import settings
from app.api.auth import router as auth_router
from app.api.ingestion import router as ingestion_router
from app.api.workflows import router as workflows_router
from app.api.evaluation import router as evaluation_router
from app.api.audit import router as audit_router
from app.core.logging import structured_logger
from app.event_driven.pubsub_handler import event_bus
from app.data_ingestion.erp_connector import erp_connector

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure ERP database seeded
    erp_connector.seed_initial_erp_data()
    # Start event bus background worker
    worker_task = asyncio.create_task(event_bus.start_worker())
    structured_logger.log_audit_event(
        event_type="SYSTEM_STARTUP",
        user="system",
        role="system",
        action="startup",
        resource="fastapi_service",
        details={"environment": settings.ENVIRONMENT, "port": settings.PORT}
    )
    yield
    # Shutdown
    event_bus._is_worker_running = False
    worker_task.cancel()
    structured_logger.log_audit_event(
        event_type="SYSTEM_SHUTDOWN",
        user="system",
        role="system",
        action="shutdown",
        resource="fastapi_service"
    )

app = FastAPI(
    title="AI Data Integration & Workflow Intelligence Platform",
    description="Enterprise Multi-Agent Platform integrating ERP databases, BigQuery, and unstructured data into Pinecone semantic indexes with CrewAI autonomous workflows and evaluation observability.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit Request Middleware
@app.middleware("http")
async def audit_request_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response

# Include API Routers
app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(workflows_router)
app.include_router(evaluation_router)
app.include_router(audit_router)

# Mount Web Dashboard
STATIC_DIR = Path("web/static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "platform": "AI Data Integration & Workflow Intelligence Platform",
        "docs": "/docs",
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "vector_backend": settings.VECTOR_STORE_BACKEND,
        "warehouse_backend": settings.WAREHOUSE_BACKEND,
        "pubsub_backend": settings.PUBSUB_BACKEND
    }

