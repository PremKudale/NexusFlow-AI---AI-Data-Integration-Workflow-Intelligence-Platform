import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.crew import crew_engine
from app.core.logging import structured_logger

STAKEHOLDER_SCENARIOS = [
    {
        "stakeholder_title": "Chief Financial Officer (CFO)",
        "name": "Dr. Alistair Vance",
        "focus_area": "Operating Margins, Cloud Infrastructure Overrun & Revenue Forecast",
        "query": "Reconcile our Q3 operating margins against cloud infrastructure spend, and identify if any supplier SLA penalty credits should be credited to Q4 financials."
    },
    {
        "stakeholder_title": "VP of Global Supply Chain Operations",
        "name": "Elena Rostova",
        "focus_area": "Supplier Reliability, Fab Delays & Critical SKU Buffer Stocks",
        "query": "Review all fab substrate delays from Silicon Foundry International for SKU-MOD-101 and verify if liquidated damages match our master SLA agreement."
    },
    {
        "stakeholder_title": "Chief Compliance & Risk Auditor",
        "name": "Marcus Thorne",
        "focus_area": "Credit Exposure, Customer Order Holds & RBAC Governance",
        "query": "Audit high-value orders currently on hold or review, verify credit limit policies against Confluence SOP, and check system tamper-evident logs."
    }
]

def main():
    print("=" * 80)
    print("TECHNICAL DISCOVERY SIMULATION WITH CUSTOMER STAKEHOLDERS")
    print("AI Data Integration & Workflow Intelligence Platform")
    print("=" * 80)

    for idx, sc in enumerate(STAKEHOLDER_SCENARIOS, 1):
        print(f"\n[{idx}/3] STAKEHOLDER: {sc['name']} - {sc['stakeholder_title']}")
        print(f"Domain Focus: {sc['focus_area']}")
        print(f"Inquiry: \"{sc['query']}\"")
        print("\n--> Launching CrewAI Multi-Agent Delegation Pipeline...")

        start = time.time()
        res = crew_engine.execute_workflow(
            query=sc["query"],
            user=f"stakeholder_{sc['name'].lower().replace(' ', '_').replace('.', '')}",
            role="analyst"
        )
        duration = round((time.time() - start) * 1000, 2)

        print(f"✓ Completed in {duration} ms | Total Tokens: {res['telemetry']['total_tokens']:,} | Cost: ${res['telemetry']['total_cost_usd']:.6f}")
        print(f"✓ Factual Consistency: {int(res['validation']['consistency_score'] * 100)}% | Audit Verdict: {res['validation']['audit_verdict']}")
        print(f"✓ Trace ID: {res['trace_id']}")

        print("\n--- SYNTHESIZED EXECUTIVE BRIEFING ---")
        brief_preview = "\n".join(res["final_report"].split("\n")[:18])
        print(brief_preview)
        print("... [Full briefing generated & logged] ...")
        print("-" * 80)

    print("\n✓ Technical discovery simulation with all 3 stakeholders completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()

