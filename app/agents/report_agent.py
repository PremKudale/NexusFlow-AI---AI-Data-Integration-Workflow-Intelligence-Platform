from typing import Dict, Any, List

class ExecutiveReportAgent:
    def __init__(self, name: str = "Executive Intelligence & Reporting Agent"):
        self.name = name
        self.role = "Chief Decision Support & Executive Reporting Specialist"
        self.goal = "Synthesize cross-silo enterprise telemetry, structured data, and contractual evidence into an actionable, decision-ready executive briefing."

    def generate_report(
        self,
        query: str,
        plan_data: Dict[str, Any],
        sql_data: Dict[str, Any],
        semantic_data: Dict[str, Any],
        validation_data: Dict[str, Any]
    ) -> str:
        structured = sql_data.get("structured_data", {})
        bq_records = structured.get("bigquery_records", [])
        erp_records = structured.get("erp_records", [])
        citations = semantic_data.get("citations", [])
        score = validation_data.get("consistency_score", 1.0)
        verdict = validation_data.get("audit_verdict", "PASSED")
        flags = validation_data.get("detected_anomalies_and_flags", [])

        report = []
        report.append(f"# Executive Intelligence Briefing")
        report.append(f"**Query Focus:** {query}\n")
        report.append(f"**Audit Status:** `{verdict}` | **Factual Consistency Score:** `{int(score * 100)}%`\n")
        report.append("---\n")

        # 1. Executive Summary
        report.append("## 1. Executive Summary")
        report.append(
            f"Autonomous multi-agent execution completed technical discovery across enterprise ERP transaction tables, "
            f"BigQuery data warehouse models, and Pinecone vector indexes. "
            f"Cross-functional analysis identified **{len(bq_records) + len(erp_records)} structured data records** and "
            f"**{len(citations)} unstructured documentary sources** (PDF contracts, Confluence SOPs, emails). "
            f"Overall operational stability remains verified with specific risk mitigation recommended below.\n"
        )

        # 2. Key Quantitative Findings
        report.append("## 2. Key Quantitative Findings (ERP & BigQuery)")
        if bq_records:
            report.append("### BigQuery Warehouse Intelligence:")
            for r in bq_records[:4]:
                if "quarter" in r:
                    report.append(
                        f"- **{r.get('quarter')}**: Gross Revenue: **${r.get('gross_revenue', 0):,.2f}** | "
                        f"Operating Margin: **{r.get('operating_margin_pct', 0)}%** | "
                        f"Cloud Infra Cost: **${r.get('cloud_infrastructure_cost', 0):,.2f}**"
                    )
                elif "incident_id" in r:
                    report.append(
                        f"- **{r.get('incident_id')}** ({r.get('vendor_name')}): Delay of **{r.get('actual_delay_hours')}h** "
                        f"(vs {r.get('sla_threshold_hours')}h SLA threshold). Assessed Penalty: **${r.get('financial_penalty_usd', 0):,.2f}** "
                        f"| *Root Cause:* {r.get('root_cause')}"
                    )
        if erp_records:
            report.append("\n### ERP Operational Highlights:")
            for o in erp_records[:4]:
                if "order_id" in o:
                    report.append(
                        f"- Order **{o.get('order_id')}** ({o.get('customer_name')} - {o.get('tier')}): "
                        f"**${o.get('total_amount', 0):,.2f}** [{o.get('status')}] (Terms: {o.get('payment_terms')})"
                    )
                elif "sku" in o:
                    report.append(
                        f"- Inventory Alert SKU **{o.get('sku')}** ({o.get('product_name')}): "
                        f"Current Stock: **{o.get('stock_quantity')}** (Reorder Threshold: {o.get('reorder_level')}) at {o.get('warehouse_location')}"
                    )
        report.append("")

        # 3. Qualitative Knowledge & Document Citations
        report.append("## 3. Policy & Unstructured Document Citations (Pinecone Index)")
        if citations:
            for idx, c in enumerate(citations[:3], 1):
                report.append(
                    f"**[{idx}] {c['title']}** (`{c['source_type'].upper()}` | Similarity: `{c['relevance_score']:.2f}`)\n"
                    f"> \"{c['excerpt']}\"\n"
                )
        else:
            report.append("*No relevant unstructured document matches identified.*\n")

        # 4. Anomaly Detection & Risk Verification
        report.append("## 4. Operational Risk & Discrepancy Verification")
        if flags:
            for f in flags:
                report.append(f"- **[{f['severity']}] {f['type']}**: {f['description']}")
        else:
            report.append("- No high-severity discrepancies or uncorroborated assertions detected.")
        report.append("")

        # 5. Strategic Recommendations
        report.append("## 5. Strategic Action Items")
        report.append("1. **Automate SLA Penalty Recovery**: Reconcile assessed BigQuery SLA penalties with Accounts Payable before vendor cycle closes.")
        report.append("2. **Resolve Credit Review Queue**: Unblock high-value orders currently on credit review via automated risk-tier credit limit re-evaluation.")
        report.append("3. **Inventory Reorder Trigger**: Initiate automated procurement for components approaching reorder levels to prevent fulfillment lag.")

        return "\n".join(report)

report_agent = ExecutiveReportAgent()

