from typing import List, Dict, Any

BENCHMARK_TEST_SUITE: List[Dict[str, Any]] = [
    {
        "id": "BENCH-001",
        "category": "Financial & Cloud Warehouse",
        "query": "What were our gross revenues and operating margin percentages for Q3-2026 vs Q2-2026, and how much did cloud infrastructure cost?",
        "ground_truth": {
            "expected_q3_revenue": 5310000.0,
            "expected_q2_revenue": 4820000.0,
            "expected_q3_margin": 48.7,
            "expected_q3_cloud_cost": 490000.0,
            "key_entities": ["Q3-2026", "Q2-2026", "operating_margin_pct", "cloud_infrastructure_cost"]
        },
        "target_source_types": ["bigquery", "spreadsheet"]
    },
    {
        "id": "BENCH-002",
        "category": "Supply Chain & SLA Enforcement",
        "query": "Identify all supplier SLA breaches in Q3-2026, the assessed financial penalties, and the root causes cited.",
        "ground_truth": {
            "expected_breaches": ["BREACH-801", "BREACH-802"],
            "expected_vendors": ["Silicon Foundry International", "Apex Precision Enclosures"],
            "total_penalties": 21000.0,
            "key_entities": ["Substrate fab raw material shortage", "Port customs clearance inspection backlog"]
        },
        "target_source_types": ["bigquery", "confluence", "pdf"]
    },
    {
        "id": "BENCH-003",
        "category": "ERP Orders & Credit Exposure",
        "query": "Which customers have orders currently on hold or review, what are their total amounts, and what are their payment terms?",
        "ground_truth": {
            "expected_orders": ["ORD-2026-8805", "ORD-2026-8804"],
            "expected_customers": ["Meridian Retail Global", "Pacific Rim Cloud Services"],
            "key_entities": ["On Hold - Credit Review", "Pending Approval", "Net-30", "Net-60"]
        },
        "target_source_types": ["erp", "email"]
    },
    {
        "id": "BENCH-004",
        "category": "Inventory Critical Reorder",
        "query": "What hardware inventory SKUs are approaching or below reorder levels in Austin and Frankfurt data centers?",
        "ground_truth": {
            "expected_skus": ["SKU-SRV-901", "SKU-SRV-902", "SKU-NET-302"],
            "key_entities": ["Austin-TX-DC1", "Frankfurt-DE-DC2", "stock_quantity", "reorder_level"]
        },
        "target_source_types": ["erp"]
    }
]

