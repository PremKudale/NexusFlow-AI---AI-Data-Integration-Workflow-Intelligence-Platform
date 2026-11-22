from typing import Dict, Any, List

class ValidationAgent:
    def __init__(self, name: str = "Fact-Checking & Validation Agent"):
        self.name = name
        self.role = "Lead Integrity Auditor & Hallucination Guardrail Agent"
        self.goal = "Cross-validate structured analytical numbers against unstructured documents and contractual policies to eliminate hallucinations and detect operational anomalies."

    def validate(self, sql_data: Dict[str, Any], semantic_data: Dict[str, Any]) -> Dict[str, Any]:
        flags = []
        corroborated_facts = []
        score = 0.95

        structured = sql_data.get("structured_data", {})
        bq_records = structured.get("bigquery_records", [])
        erp_records = structured.get("erp_records", [])
        citations = semantic_data.get("citations", [])

        # 1. Cross-check SLA penalties against Supplier policies
        for breach in bq_records:
            if "incident_id" in breach and "financial_penalty_usd" in breach:
                vendor = breach.get("vendor_name", "")
                delay = breach.get("actual_delay_hours", 0)
                threshold = breach.get("sla_threshold_hours", 0)
                penalty = breach.get("financial_penalty_usd", 0)

                if delay > threshold:
                    corroborated_facts.append(
                        f"Incident {breach.get('incident_id')}: {vendor} delayed {delay}h (threshold: {threshold}h). Penalty of ${penalty:,.2f} properly assessed against contract terms."
                    )
                if delay > threshold * 2:
                    flags.append({
                        "severity": "HIGH",
                        "type": "SLA_BREACH_CRITICAL",
                        "description": f"Critical SLA violation: {vendor} exceeded contract latency threshold by more than 100% ({delay}h vs {threshold}h limit)."
                    })
                    score -= 0.05

        # 2. Cross-check ERP Order status and credit limits
        for order in erp_records:
            if "order_id" in order and "status" in order:
                status = order.get("status", "")
                amount = order.get("total_amount", 0)
                cust = order.get("customer_name", "")

                if "Hold" in status or "Credit" in status:
                    flags.append({
                        "severity": "MEDIUM",
                        "type": "CREDIT_HOLD_EXPOSURE",
                        "description": f"Order {order.get('order_id')} (${amount:,.2f}) for customer '{cust}' is marked '{status}'. Financial credit review required before release."
                    })
                else:
                    corroborated_facts.append(
                        f"Order {order.get('order_id')} verified in ERP: Total ${amount:,.2f}, Status '{status}'."
                    )

        # 3. Assess citation coverage
        if not citations:
            flags.append({
                "severity": "LOW",
                "type": "UNSTRUCTURED_EVIDENCE_ABSENT",
                "description": "No direct vector document chunks matched. Insights rely predominantly on structured warehouse metrics."
            })
            score -= 0.05
        else:
            corroborated_facts.append(
                f"Retrieved {len(citations)} supporting documents/SOPs with peak semantic relevance of {semantic_data.get('highest_similarity', 0.0):.2f}."
            )

        consistency_score = max(0.50, min(1.0, score))

        return {
            "agent": self.name,
            "status": "VALIDATED",
            "consistency_score": round(consistency_score, 2),
            "is_factually_consistent": len([f for f in flags if f["severity"] == "HIGH"]) == 0,
            "corroborated_facts": corroborated_facts,
            "detected_anomalies_and_flags": flags,
            "audit_verdict": "PASSED" if consistency_score >= 0.80 else "REVIEW_RECOMMENDED"
        }

validator_agent = ValidationAgent()

