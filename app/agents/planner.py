import json
import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SubTaskPlan(BaseModel):
    task_id: str
    assigned_agent: str
    description: str
    expected_output_type: str  # 'sql_analysis', 'semantic_retrieval', 'fact_validation', 'report_generation'
    dependencies: List[str] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    objective: str
    strategy: str
    tasks: List[SubTaskPlan]

class PlannerAgent:
    def __init__(self, name: str = "Chief Planning Agent"):
        self.name = name
        self.role = "Lead Strategic Planning & Workflow Orchestrator"
        self.goal = "Decompose ambiguous business inquiries into precise, executable multi-agent workflows."

    def plan(self, user_query: str) -> ExecutionPlan:
        query_lower = user_query.lower()

        # Autonomous task delegation logic based on intent analysis
        tasks = []

        # 1. Always plan structured analytics if query mentions revenue, orders, inventory, margins, costs, SLA, breaches
        tasks.append(SubTaskPlan(
            task_id="task_1_structured_analytics",
            assigned_agent="SQL & Data Analytics Agent",
            description=f"Query ERP database and BigQuery analytical warehouse to gather structured metrics related to: '{user_query}'",
            expected_output_type="sql_analysis",
            dependencies=[]
        ))

        # 2. Plan semantic document search across contracts, Confluence, emails, and PDFs
        tasks.append(SubTaskPlan(
            task_id="task_2_semantic_search",
            assigned_agent="Semantic Knowledge Agent",
            description=f"Retrieve unstructured context (contracts, Confluence SOPs, emails) from Pinecone vector index regarding: '{user_query}'",
            expected_output_type="semantic_retrieval",
            dependencies=[]
        ))

        # 3. Plan cross-validation & fact verification
        tasks.append(SubTaskPlan(
            task_id="task_3_fact_validation",
            assigned_agent="Fact-Checking & Validation Agent",
            description="Reconcile structured query metrics against retrieved document clauses to verify consistency and detect discrepancies.",
            expected_output_type="fact_validation",
            dependencies=["task_1_structured_analytics", "task_2_semantic_search"]
        ))

        # 4. Plan executive report synthesis
        tasks.append(SubTaskPlan(
            task_id="task_4_report_synthesis",
            assigned_agent="Executive Reporting Agent",
            description="Synthesize structured analytics, document citations, and validation scores into a decision-ready executive briefing.",
            expected_output_type="report_generation",
            dependencies=["task_3_fact_validation"]
        ))

        strategy_desc = (
            "Hierarchical cross-functional workflow: parallel structured SQL analytics and semantic vector search, "
            "followed by rigorous validation and executive briefing generation."
        )

        return ExecutionPlan(
            objective=user_query,
            strategy=strategy_desc,
            tasks=tasks
        )

planner_agent = PlannerAgent()

