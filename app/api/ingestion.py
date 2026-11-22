import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from config.rbac import Permission
from app.core.security import require_permission, UserSession
from app.data_ingestion.doc_extractors import doc_extractor, SemanticDocumentChunk
from app.data_ingestion.vector_store import vector_store
from app.data_ingestion.erp_connector import erp_connector
from app.core.logging import structured_logger
from app.event_driven.pubsub_handler import event_bus

router = APIRouter(prefix="/api/ingest", tags=["Data Ingestion & Semantic Indexing"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class ConfluenceIngestRequest(BaseModel):
    title: str
    space_key: str
    markdown_content: str
    page_id: str

class EmailIngestRequest(BaseModel):
    email_id: str
    subject: str
    sender: str
    content: str

class RestApiIngestRequest(BaseModel):
    endpoint_name: str
    payload: Dict[str, Any]

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserSession = Depends(require_permission(Permission.DATA_INGEST))
):
    dest_path = UPLOAD_DIR / file.filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ext = dest_path.suffix.lower()
    chunks: List[SemanticDocumentChunk] = []

    if ext == ".pdf":
        chunks = doc_extractor.extract_pdf(str(dest_path), tenant_id=current_user.tenant_id)
    elif ext in [".csv", ".xlsx", ".xls"]:
        chunks = doc_extractor.extract_spreadsheet(str(dest_path), tenant_id=current_user.tenant_id)
    else:
        # Text/Markdown fallback
        with open(dest_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        chunks = doc_extractor.extract_confluence_page(
            title=dest_path.stem,
            space="DOCUMENT_UPLOAD",
            markdown_content=text,
            page_id=dest_path.stem,
            tenant_id=current_user.tenant_id
        )

    indexed_count = vector_store.upsert_chunks(chunks)

    # Publish ingestion event
    await event_bus.publish(
        topic="data-ingestion",
        data={
            "file_name": file.filename,
            "chunks_indexed": indexed_count,
            "user": current_user.username
        }
    )

    structured_logger.log_audit_event(
        event_type="INGESTION_FILE_UPLOAD",
        user=current_user.username,
        role=current_user.role.value,
        action="upload_and_index",
        resource=file.filename,
        details={"chunks": indexed_count, "format": ext}
    )

    return {
        "status": "SUCCESS",
        "file_name": file.filename,
        "chunks_indexed": indexed_count,
        "vector_store_backend": vector_store.backend
    }

@router.post("/confluence")
async def ingest_confluence(
    payload: ConfluenceIngestRequest,
    current_user: UserSession = Depends(require_permission(Permission.DATA_INGEST))
):
    chunks = doc_extractor.extract_confluence_page(
        title=payload.title,
        space=payload.space_key,
        markdown_content=payload.markdown_content,
        page_id=payload.page_id,
        tenant_id=current_user.tenant_id
    )
    indexed_count = vector_store.upsert_chunks(chunks)
    return {"status": "SUCCESS", "page_id": payload.page_id, "chunks_indexed": indexed_count}

@router.post("/email")
async def ingest_email(
    payload: EmailIngestRequest,
    current_user: UserSession = Depends(require_permission(Permission.DATA_INGEST))
):
    raw_content = f"From: {payload.sender}\nSubject: {payload.subject}\nDate: 2026-11-20\n\n{payload.content}"
    chunks = doc_extractor.extract_email(
        content_str=raw_content,
        email_id=payload.email_id,
        tenant_id=current_user.tenant_id
    )
    indexed_count = vector_store.upsert_chunks(chunks)
    return {"status": "SUCCESS", "email_id": payload.email_id, "chunks_indexed": indexed_count}

@router.post("/rest-api")
async def ingest_rest_api_payload(
    payload: RestApiIngestRequest,
    current_user: UserSession = Depends(require_permission(Permission.DATA_INGEST))
):
    chunks = doc_extractor.extract_rest_api_payload(
        endpoint_name=payload.endpoint_name,
        payload=payload.payload,
        tenant_id=current_user.tenant_id
    )
    indexed_count = vector_store.upsert_chunks(chunks)
    return {"status": "SUCCESS", "endpoint": payload.endpoint_name, "chunks_indexed": indexed_count}

@router.post("/erp/sync")
async def sync_erp_database(
    current_user: UserSession = Depends(require_permission(Permission.DATA_INGEST))
):
    erp_connector.seed_initial_erp_data()
    structured_logger.log_audit_event(
        event_type="ERP_SYNC",
        user=current_user.username,
        role=current_user.role.value,
        action="erp_sync",
        resource="erp_system.db"
    )
    return {"status": "SUCCESS", "message": "ERP transactional tables synchronized."}

@router.get("/stats")
async def get_ingestion_stats(
    current_user: UserSession = Depends(require_permission(Permission.DATA_READ))
):
    return vector_store.get_stats()

