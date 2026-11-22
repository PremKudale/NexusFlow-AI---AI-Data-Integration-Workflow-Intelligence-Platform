import time
from typing import Dict, Any, Optional
from app.agents.planner import planner_agent
from app.agents.sql_agent import sql_agent
from app.agents.vector_agent import vector_agent
from app.agents.validator_agent import validator_agent
from app.agents.report_agent import report_agent
from app.core.telemetry import telemetry, ExecutionTrace
from app.core.logging import structured_logger

class CrewWorkflowEngine:
    def __init__(self):
        self.crew_name = "Enterprise Intelligence Multi-Agent Crew"

    def execute_workflow(
        self,
        query: str,
        user: str = "analyst_jane",
        role: str = "analyst",
        session_id: str = "session_001"
    ) -> Dict[str, Any]:
        # 1. Start overall execution trace
        trace = telemetry.start_trace(
            query=query,
            session_id=session_id,
            workflow_type="crewai_multi_agent"
        )

        structured_logger.log_audit_event(
            event_type="WORKFLOW_START",
            user=user,
            role=role,
            action="execute_workflow",
            resource=f"query: {query[:50]}...",
            request_id=trace.trace_id
        )

        # -------------------------------------------------------------
        # Step 1: Planning Agent
        # -------------------------------------------------------------
        span_plan = telemetry.start_span(
            trace_id=trace.trace_id,
            span_name="Strategic Planning & Decomposition",
            agent_name=planner_agent.name
        )
        t0 = time.time()
        plan = planner_agent.plan(user_query=query)
        # Synthetic token accounting for deterministic evaluation
        prompt_tok_1 = len(query.split()) * 12 + 150
        comp_tok_1 = len(plan.strategy.split()) * 4 + 80
        telemetry.finish_span(
            span=span_plan,
            prompt_tokens=prompt_tok_1,
            completion_tokens=comp_tok_1,
            metadata_update={"tasks_count": len(plan.tasks)}
        )

        # -------------------------------------------------------------
        # Step 2: SQL & Data Analytics Agent
        # -------------------------------------------------------------
        span_sql = telemetry.start_span(
            trace_id=trace.trace_id,
            span_name="Structured Warehouse & ERP Analytics",
            agent_name=sql_agent.name
        )
        sql_out = sql_agent.execute_analytics(query=query)
        prompt_tok_2 = 250 + len(query.split()) * 5
        comp_tok_2 = 180 + sql_out["summary_metrics"]["total_rows_retrieved"] * 15
        telemetry.finish_span(
            span=span_sql,
            prompt_tokens=prompt_tok_2,
            completion_tokens=comp_tok_2,
            metadata_update={"rows": sql_out["summary_metrics"]["total_rows_retrieved"]}
        )

        # -------------------------------------------------------------
        # Step 3: Semantic Knowledge Agent (Pinecone retrieval)
        # -------------------------------------------------------------
        span_vec = telemetry.start_span(
            trace_id=trace.trace_id,
            span_name="Unstructured Semantic Index Retrieval",
            agent_name=vector_agent.name
        )
        vec_out = vector_agent.search_knowledge(query=query, top_k=4)
        prompt_tok_3 = 180 + len(query.split()) * 6
        comp_tok_3 = 120 + vec_out["citations_found"] * 45
        telemetry.finish_span(
            span=span_vec,
            prompt_tokens=prompt_tok_3,
            completion_tokens=comp_tok_3,
            metadata_update={"citations": vec_out["citations_found"]}
        )

        # -------------------------------------------------------------
        # Step 4: Fact-Checking & Validation Agent
        # -------------------------------------------------------------
        span_val = telemetry.start_span(
            trace_id=trace.trace_id,
            span_name="Fact Cross-Validation & Hallucination Guardrail",
            agent_name=validator_agent.name
        )
        val_out = validator_agent.validate(sql_data=sql_out, semantic_data=vec_out)
        prompt_tok_4 = comp_tok_2 + comp_tok_3 + 120
        comp_tok_4 = 110 + len(val_out["corroborated_facts"]) * 20
        telemetry.finish_span(
            span=span_val,
            prompt_tokens=prompt_tok_4,
            completion_tokens=comp_tok_4,
            metadata_update={"verdict": val_out["audit_verdict"], "score": val_out["consistency_score"]}
        )

        # -------------------------------------------------------------
        # Step 5: Executive Reporting Agent
        # -------------------------------------------------------------
        span_rep = telemetry.start_span(
            trace_id=trace.trace_id,
            span_name="Executive Briefing Synthesis",
            agent_name=report_agent.name
        )
        final_markdown_report = report_agent.generate_report(
            query=query,
            plan_data=plan.model_dump(),
            sql_data=sql_out,
            semantic_data=vec_out,
            validation_data=val_out
        )
        prompt_tok_5 = 350 + comp_tok_4
        comp_tok_5 = len(final_markdown_report.split()) * 2
        telemetry.finish_span(
            span=span_rep,
            prompt_tokens=prompt_tok_5,
            completion_tokens=comp_tok_5,
            metadata_update={"report_length": len(final_markdown_report)}
        )

        # -------------------------------------------------------------
        # Evaluation Metrics calculation for this run
        # -------------------------------------------------------------
        eval_metrics = {
            "answer_correctness": round(val_out["consistency_score"], 4),
            "retrieval_recall": round(min(1.0, vec_out["citations_found"] / 3.0), 4),
            "factual_consistency": val_out["audit_verdict"] == "PASSED",
            "anomalies_detected": len(val_out["detected_anomalies_and_flags"])
        }

        # Finish trace
        finished_trace = telemetry.finish_trace(
            trace_id=trace.trace_id,
            final_output=final_markdown_report,
            eval_metrics=eval_metrics
        )

        structured_logger.log_audit_event(
            event_type="WORKFLOW_COMPLETE",
            user=user,
            role=role,
            action="execute_workflow",
            resource=f"trace_id: {trace.trace_id}",
            status="SUCCESS",
            details={
                "duration_ms": finished_trace.total_duration_ms,
                "total_tokens": finished_trace.total_tokens,
                "cost_usd": finished_trace.total_cost_usd,
                "verdict": val_out["audit_verdict"]
            },
            request_id=trace.trace_id
        )

        return {
            "trace_id": trace.trace_id,
            "query": query,
            "final_report": final_markdown_report,
            "plan": plan.model_dump(),
            "validation": val_out,
            "telemetry": {
                "duration_ms": finished_trace.total_duration_ms,
                "total_tokens": finished_trace.total_tokens,
                "prompt_tokens": finished_trace.total_prompt_tokens,
                "completion_tokens": finished_trace.total_completion_tokens,
                "tokens_per_sec": finished_trace.avg_tokens_per_sec,
                "total_cost_usd": finished_trace.total_cost_usd,
                "spans": [s.model_dump() for s in finished_trace.spans]
            },
            "evaluation_metrics": eval_metrics
        }

crew_engine = CrewWorkflowEngine()

