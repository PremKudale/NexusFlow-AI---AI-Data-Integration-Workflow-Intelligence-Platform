import json
import base64
from typing import Dict, Any
from app.data_ingestion.doc_extractors import doc_extractor
from app.data_ingestion.vector_store import vector_store
from app.agents.crew import crew_engine
from app.core.logging import structured_logger

def gcs_file_ingestion_function(event: Dict[str, Any], context: Any):
    """
    Google Cloud Function: Cloud Storage Eventarc Trigger
    Invoked when a PDF/CSV/Excel file lands in the ingestion bucket.
    """
    file_name = event.get("name", "unknown_file")
    bucket_name = event.get("bucket", "enterprise-intelligence-ingest")
    content_type = event.get("contentType", "application/pdf")

    structured_logger.log_audit_event(
        event_type="CLOUD_FUNCTION_GCS_TRIGGER",
        user="cloud_functions_runtime",
        role="system",
        action="ingest_gcs_document",
        resource=f"gs://{bucket_name}/{file_name}",
        details={"content_type": content_type}
    )

    return {"status": "ACK", "file": file_name, "message": "Queued for semantic vectorization"}

def erp_cdc_stream_function(event: Dict[str, Any], context: Any):
    """
    Google Cloud Function: Change Data Capture (CDC) Trigger
    Invoked when ERP updates occur in PostgreSQL or BigQuery stream.
    """
    data = event.get("data", {})
    table = data.get("table", "erp_orders")
    operation = data.get("operation", "UPSERT")

    structured_logger.log_audit_event(
        event_type="CLOUD_FUNCTION_ERP_CDC",
        user="cloud_functions_runtime",
        role="system",
        action=f"cdc_{operation.lower()}",
        resource=f"erp_table:{table}",
        details=data
    )

    return {"status": "SUCCESS", "table": table, "operation": operation}

def workflow_pubsub_function(event: Dict[str, Any], context: Any):
    """
    Google Cloud Function: Cloud Pub/Sub Trigger
    Asynchronously executes multi-agent workflow on Cloud Run / Cloud Functions.
    """
    if "data" in event:
        raw_data = base64.b64decode(event["data"]).decode("utf-8")
        payload = json.loads(raw_data)
    else:
        payload = event

    query = payload.get("query", "Analyze Q3 revenue and supply chain status")
    user = payload.get("user", "pubsub_subscriber")
    role = payload.get("role", "analyst")

    result = crew_engine.execute_workflow(query=query, user=user, role=role)
    return {"status": "COMPLETED", "trace_id": result["trace_id"]}

