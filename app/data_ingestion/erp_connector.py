import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config.settings import settings

ERP_DB_PATH = Path("data/erp/erp_system.db")
ERP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class ERPConnector:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(ERP_DB_PATH)
        self._initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Customers / Accounts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS erp_customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tier TEXT NOT NULL,
                region TEXT NOT NULL,
                credit_limit REAL NOT NULL,
                outstanding_balance REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Products & Inventory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS erp_inventory (
                sku TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL,
                reorder_level INTEGER NOT NULL,
                lead_time_days INTEGER NOT NULL,
                warehouse_location TEXT NOT NULL
            )
        """)

        # 3. Orders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS erp_orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                fulfillment_date TEXT,
                payment_terms TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES erp_customers (customer_id)
            )
        """)

        # 4. Order Line Items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS erp_order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount REAL DEFAULT 0.0,
                FOREIGN KEY (order_id) REFERENCES erp_orders (order_id),
                FOREIGN KEY (sku) REFERENCES erp_inventory (sku)
            )
        """)

        # 5. Suppliers & SLAs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS erp_suppliers (
                supplier_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                on_time_delivery_rate REAL NOT NULL,
                quality_rating REAL NOT NULL,
                sla_penalty_clause TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def seed_initial_erp_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Seed Customers
        customers = [
            ("CUST-1001", "Apex Logistics Corp", "Enterprise", "North America", 500000.0, 124500.0),
            ("CUST-1002", "Nexus Healthcare Systems", "Strategic", "North America", 1000000.0, 310200.0),
            ("CUST-1003", "Vanguard Manufacturing EMEA", "Enterprise", "Europe", 750000.0, 89000.0),
            ("CUST-1004", "Pacific Rim Cloud Services", "Standard", "APAC", 250000.0, 15300.0),
            ("CUST-1005", "Meridian Retail Global", "Strategic", "North America", 1200000.0, 420000.0),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO erp_customers (customer_id, name, tier, region, credit_limit, outstanding_balance)
            VALUES (?, ?, ?, ?, ?, ?)
        """, customers)

        # Seed Inventory
        inventory = [
            ("SKU-SRV-901", "Titan Edge Server Gen 4", "Hardware", 12500.0, 42, 20, 14, "Austin-TX-DC1"),
            ("SKU-SRV-902", "Quantum Blade Rack 42U", "Hardware", 28000.0, 18, 10, 21, "Austin-TX-DC1"),
            ("SKU-NET-301", "FiberOptic 400G Core Switch", "Networking", 8500.0, 65, 30, 10, "Frankfurt-DE-DC2"),
            ("SKU-NET-302", "Terabit Routing Gateway", "Networking", 19200.0, 12, 15, 30, "Frankfurt-DE-DC2"),
            ("SKU-MOD-101", "High-Bandwidth AI Accelerator", "Components", 4200.0, 150, 50, 45, "Taipei-TW-DC3"),
            ("SKU-PWR-501", "Redundant Industrial UPS 20kW", "Power", 6400.0, 28, 10, 14, "Austin-TX-DC1"),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO erp_inventory (sku, product_name, category, unit_price, stock_quantity, reorder_level, lead_time_days, warehouse_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, inventory)

        # Seed Orders
        orders = [
            ("ORD-2026-8801", "CUST-1001", "2026-10-15", 75000.0, "Delivered", "2026-10-22", "Net-30"),
            ("ORD-2026-8802", "CUST-1002", "2026-11-02", 340000.0, "Processing", None, "Net-45"),
            ("ORD-2026-8803", "CUST-1003", "2026-11-10", 128000.0, "Delivered", "2026-11-18", "Net-30"),
            ("ORD-2026-8804", "CUST-1004", "2026-11-14", 45000.0, "Pending Approval", None, "Net-60"),
            ("ORD-2026-8805", "CUST-1005", "2026-11-19", 215000.0, "On Hold - Credit Review", None, "Net-30"),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO erp_orders (order_id, customer_id, order_date, total_amount, status, fulfillment_date, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, orders)

        # Seed Order Line Items
        items = [
            ("ORD-2026-8801", "SKU-SRV-901", 6, 12500.0, 0.0),
            ("ORD-2026-8802", "SKU-SRV-902", 10, 28000.0, 0.05),
            ("ORD-2026-8802", "SKU-NET-301", 8, 8500.0, 0.0),
            ("ORD-2026-8803", "SKU-NET-302", 6, 19200.0, 0.0),
            ("ORD-2026-8804", "SKU-MOD-101", 10, 4200.0, 0.0),
            ("ORD-2026-8805", "SKU-SRV-901", 12, 12500.0, 0.08),
            ("ORD-2026-8805", "SKU-PWR-501", 10, 6400.0, 0.0),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO erp_order_items (order_id, sku, quantity, unit_price, discount)
            VALUES (?, ?, ?, ?, ?)
        """, items)

        # Seed Suppliers
        suppliers = [
            ("SUP-501", "Silicon Foundry International", "Components", 0.94, 4.8, "5% penalty per week delay past delivery date"),
            ("SUP-502", "OpticLink Global Network", "Networking", 0.98, 4.9, "Full replacement within 48h and 10% credit"),
            ("SUP-503", "Apex Precision Enclosures", "Hardware", 0.88, 4.2, "2% penalty for late shipment; lead time guarantee 21 days"),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO erp_suppliers (supplier_id, name, category, on_time_delivery_rate, quality_rating, sla_penalty_clause)
            VALUES (?, ?, ?, ?, ?, ?)
        """, suppliers)

        conn.commit()
        conn.close()

    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        # Safety check: enforce read-only analytical queries
        disallowed = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        query_upper = sql_query.upper().strip()
        for kw in disallowed:
            if kw in query_upper:
                raise ValueError(f"Unsafe SQL execution blocked: Keyword '{kw}' is prohibited.")

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        return result

    def get_schema_summary(self) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        summary = []
        for t in tables:
            summary.append(f"Table: {t['name']}\nDDL: {t['sql']}\n")
        conn.close()
        return "\n".join(summary)

erp_connector = ERPConnector()

