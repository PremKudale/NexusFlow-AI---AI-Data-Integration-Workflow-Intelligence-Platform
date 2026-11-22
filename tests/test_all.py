import pytest
import asyncio
from app.data_ingestion.erp_connector import erp_connector
from app.data_ingestion.bigquery_client import bigquery_client
from app.data_ingestion.doc_extractors import doc_extractor
from app.data_ingestion.embeddings import embedding_service
from app.data_ingestion.vector_store import vector_store
from app.agents.crew import crew_engine
from app.agents.planner import planner_agent
from app.evaluation.pipeline import eval_pipeline
from app.core.security import create_access_token, decode_access_token, verify_password, get_password_hash, DEMO_USERS
from config.rbac import Role, Permission, verify_role_has_permission
from app.event_driven.retry_manager import retry_manager, dlq

def test_erp_and_warehouse():
    erp_connector.seed_initial_erp_data()
    customers = erp_connector.execute_query("SELECT * FROM erp_customers;")
    assert len(customers) >= 5

    inventory = erp_connector.execute_query("SELECT * FROM erp_inventory;")
    assert len(inventory) >= 6

    bq_summary = bigquery_client.query("SELECT * FROM quarterly_revenue_summary;")
    assert len(bq_summary) >= 4

def test_document_extraction_and_vector_store():
    email_text = "From: vendor@fab.com\nSubject: Wafer Delay Notice\nDate: 2026-11-20\n\nSubstrate raw material shortage."
    chunks = doc_extractor.extract_email(email_text, email_id="TEST-EML-01")
    assert len(chunks) == 1
    assert chunks[0].source_type == "email"

    conf_chunks = doc_extractor.extract_confluence_page(
        title="Credit Review Policy",
        space="FINANCE",
        markdown_content="Orders over $100,000 require CFO authorization.",
        page_id="CONF-01"
    )
    assert len(conf_chunks) == 1

    count = vector_store.upsert_chunks(chunks + conf_chunks)
    assert count == 2

    # Vector similarity search
    results = vector_store.search("substrate raw material shortage", top_k=2)
    assert len(results) > 0
    assert "substrate" in results[0].content.lower()

def test_planner_and_crew_workflow():
    query = "What were our gross revenues for Q3-2026 and were there any supplier delays?"
    plan = planner_agent.plan(user_query=query)
    assert len(plan.tasks) == 4

    result = crew_engine.execute_workflow(query=query, user="test_user", role="analyst")
    assert "final_report" in result
    assert result["validation"]["audit_verdict"] in ["PASSED", "REVIEW_RECOMMENDED"]
    assert result["telemetry"]["duration_ms"] > 0
    assert result["telemetry"]["total_tokens"] > 0
    assert result["telemetry"]["total_cost_usd"] > 0
    assert len(result["telemetry"]["spans"]) == 5

def test_evaluation_pipeline():
    summary = eval_pipeline.run_benchmark_suite(limit=2)
    assert summary["tests_executed"] == 2
    agg = summary["aggregate_metrics"]
    assert agg["answer_correctness"] > 0.0
    assert agg["retrieval_recall"] > 0.0
    assert agg["avg_tokens_per_sec"] > 0.0
    assert agg["total_cost_usd"] > 0.0

def test_rbac_and_jwt_security():
    # Role permissions
    assert verify_role_has_permission(Role.ADMIN, Permission.DATA_DELETE) is True
    assert verify_role_has_permission(Role.VIEWER, Permission.DATA_DELETE) is False
    assert verify_role_has_permission(Role.ANALYST, Permission.WORKFLOW_EXECUTE) is True

    # JWT Tokens
    token = create_access_token(data={"sub": "admin", "role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"

def test_retry_and_dlq():
    fail_counter = {"count": 0}

    def flaky_task(msg):
        fail_counter["count"] += 1
        if fail_counter["count"] < 2:
            raise ValueError("Transient network glitch")
        return "SUCCESS"

    from app.event_driven.retry_manager import RetryManager
    fast_retry = RetryManager(max_retries=3, initial_delay=0.01, backoff_factor=1.5)

    res = fast_retry.execute_sync(flaky_task, {"id": "msg_01"})
    assert res == "SUCCESS"
    assert fail_counter["count"] == 2

