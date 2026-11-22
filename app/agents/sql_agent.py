import re
from typing import Dict, Any, List
from app.data_ingestion.erp_connector import erp_connector
from app.data_ingestion.bigquery_client import bigquery_client

class SQLAnalyticsAgent:
    def __init__(self, name: str = "Enterprise SQL & Data Analytics Agent"):
        self.name = name
        self.role = "Senior Data Analytics & SQL Engineer"
        self.goal = "Formulate safe, optimized analytical queries over ERP and BigQuery systems to extract precise numerical facts."

    def execute_analytics(self, query: str) -> Dict[str, Any]:
        query_l = query.lower()
        erp_results = []
        bq_results = []
        executed_sqls = []

        # 1. Determine relevant BigQuery queries
        if any(w in query_l for w in ["revenue", "quarter", "margin", "cogs", "growth", "financial", "q3", "q4", "2026"]):
            bq_sql = """
                SELECT quarter, gross_revenue, cogs, operating_margin_pct, cloud_infrastructure_cost, hardware_deliveries_count
                FROM quarterly_revenue_summary
                ORDER BY year ASC, quarter ASC;
            """
            try:
                bq_results = bigquery_client.query(bq_sql)
                executed_sqls.append({"target": "BigQuery", "sql": bq_sql.strip(), "rows": len(bq_results)})
            except Exception as e:
                executed_sqls.append({"target": "BigQuery", "error": str(e)})

        if any(w in query_l for w in ["sla", "breach", "delay", "supplier", "penalty", "vendor", "supply chain"]):
            bq_breach_sql = """
                SELECT incident_id, vendor_name, sla_threshold_hours, actual_delay_hours, financial_penalty_usd, root_cause, incident_quarter
                FROM supply_chain_sla_breaches
                ORDER BY financial_penalty_usd DESC;
            """
            try:
                breaches = bigquery_client.query(bq_breach_sql)
                bq_results.extend(breaches)
                executed_sqls.append({"target": "BigQuery", "sql": bq_breach_sql.strip(), "rows": len(breaches)})
            except Exception as e:
                executed_sqls.append({"target": "BigQuery", "error": str(e)})

        # 2. Determine relevant ERP queries
        if any(w in query_l for w in ["order", "customer", "inventory", "stock", "product", "sku", "fulfillment", "balance", "credit"]):
            erp_sql = """
                SELECT o.order_id, c.name as customer_name, c.tier, o.total_amount, o.status, o.payment_terms
                FROM erp_orders o
                JOIN erp_customers c ON o.customer_id = c.customer_id
                ORDER BY o.total_amount DESC;
            """
            try:
                erp_results = erp_connector.execute_query(erp_sql)
                executed_sqls.append({"target": "ERP Database", "sql": erp_sql.strip(), "rows": len(erp_results)})
            except Exception as e:
                executed_sqls.append({"target": "ERP Database", "error": str(e)})

            erp_inv_sql = """
                SELECT sku, product_name, category, stock_quantity, reorder_level, unit_price, warehouse_location
                FROM erp_inventory
                WHERE stock_quantity <= reorder_level * 1.5;
            """
            try:
                low_stock = erp_connector.execute_query(erp_inv_sql)
                executed_sqls.append({"target": "ERP Inventory", "sql": erp_inv_sql.strip(), "rows": len(low_stock)})
                erp_results.extend(low_stock)
            except Exception as e:
                pass

        # If no specific triggers matched, run a general health overview
        if not executed_sqls:
            general_sql = "SELECT quarter, gross_revenue, operating_margin_pct FROM quarterly_revenue_summary LIMIT 4;"
            bq_results = bigquery_client.query(general_sql)
            executed_sqls.append({"target": "BigQuery", "sql": general_sql, "rows": len(bq_results)})

        return {
            "agent": self.name,
            "status": "COMPLETED",
            "executed_queries": executed_sqls,
            "structured_data": {
                "bigquery_records": bq_results,
                "erp_records": erp_results
            },
            "summary_metrics": {
                "total_rows_retrieved": len(bq_results) + len(erp_results),
                "systems_queried": list(set(s.get("target") for s in executed_sqls if "target" in s))
            }
        }

sql_agent = SQLAnalyticsAgent()

