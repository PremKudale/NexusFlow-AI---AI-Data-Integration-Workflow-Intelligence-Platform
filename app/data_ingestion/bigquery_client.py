import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings

BQ_DIR = Path("data/bigquery")
BQ_DIR.mkdir(parents=True, exist_ok=True)
BQ_EMULATOR_DB = BQ_DIR / "bigquery_emulator.db"

class BigQueryWarehouseClient:
    def __init__(self):
        self.backend = settings.WAREHOUSE_BACKEND
        self.dataset = settings.BIGQUERY_DATASET
        self._gcp_client = None
        self._init_backend()
        self._init_emulator_tables()

    def _init_backend(self):
        if self.backend == "bigquery" and settings.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                from google.cloud import bigquery
                self._gcp_client = bigquery.Client(project=settings.GCP_PROJECT_ID)
                print(f"[BigQuery] Connected to GCP Project: {settings.GCP_PROJECT_ID}")
            except Exception as e:
                print(f"[BigQuery] Fallback to local warehouse emulator: {e}")
                self.backend = "local_warehouse"

    def _get_emulator_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(BQ_EMULATOR_DB))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_emulator_tables(self):
        conn = self._get_emulator_conn()
        cursor = conn.cursor()

        # BigQuery table: quarterly_revenue_summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_revenue_summary (
                quarter TEXT PRIMARY KEY,
                year INTEGER,
                gross_revenue REAL,
                cogs REAL,
                operating_margin_pct REAL,
                cloud_infrastructure_cost REAL,
                hardware_deliveries_count INTEGER
            )
        """)

        # BigQuery table: supply_chain_sla_breaches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supply_chain_sla_breaches (
                incident_id TEXT PRIMARY KEY,
                vendor_id TEXT,
                vendor_name TEXT,
                sla_threshold_hours INTEGER,
                actual_delay_hours INTEGER,
                financial_penalty_usd REAL,
                root_cause TEXT,
                incident_quarter TEXT
            )
        """)

        # Seed initial warehouse data
        cursor.execute("SELECT COUNT(*) FROM quarterly_revenue_summary")
        if cursor.fetchone()[0] == 0:
            quarters = [
                ("Q1-2026", 2026, 4250000.0, 2100000.0, 50.5, 410000.0, 180),
                ("Q2-2026", 2026, 4820000.0, 2350000.0, 51.2, 445000.0, 210),
                ("Q3-2026", 2026, 5310000.0, 2720000.0, 48.7, 490000.0, 245),
                ("Q4-2026", 2026, 6150000.0, 2980000.0, 51.5, 530000.0, 290)
            ]
            cursor.executemany("""
                INSERT INTO quarterly_revenue_summary VALUES (?, ?, ?, ?, ?, ?, ?)
            """, quarters)

            breaches = [
                ("BREACH-801", "SUP-501", "Silicon Foundry International", 48, 112, 14200.0, "Substrate fab raw material shortage", "Q3-2026"),
                ("BREACH-802", "SUP-503", "Apex Precision Enclosures", 72, 96, 6800.0, "Port customs clearance inspection backlog", "Q3-2026"),
                ("BREACH-803", "SUP-501", "Silicon Foundry International", 48, 80, 8500.0, "Semiconductor test assembly recalibration", "Q4-2026")
            ]
            cursor.executemany("""
                INSERT INTO supply_chain_sla_breaches VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, breaches)

        conn.commit()
        conn.close()

    def query(self, sql_query: str) -> List[Dict[str, Any]]:
        # Enforce read-only analytical warehouse query
        disallowed = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        query_upper = sql_query.upper().strip()
        for kw in disallowed:
            if kw in query_upper:
                raise ValueError(f"Unsafe BigQuery SQL execution blocked: Keyword '{kw}' is prohibited.")

        if self._gcp_client:
            try:
                query_job = self._gcp_client.query(sql_query)
                results = [dict(row) for row in query_job.result()]
                return results
            except Exception as e:
                print(f"[BigQuery] Remote query failure, falling back to local: {e}")

        # Local warehouse emulator execution
        # Replace dataset prefix if present e.g. "enterprise_analytics."
        sanitized_sql = sql_query.replace(f"{self.dataset}.", "").replace("enterprise_analytics.", "")
        conn = self._get_emulator_conn()
        cursor = conn.cursor()
        cursor.execute(sanitized_sql)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        return result

    def get_warehouse_schema(self) -> str:
        conn = self._get_emulator_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        summary = []
        for t in tables:
            summary.append(f"BigQuery Table: {self.dataset}.{t['name']}\nSchema: {t['sql']}\n")
        conn.close()
        return "\n".join(summary)

bigquery_client = BigQueryWarehouseClient()

