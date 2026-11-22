import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data_ingestion.erp_connector import erp_connector
from app.data_ingestion.bigquery_client import bigquery_client
from app.data_ingestion.doc_extractors import doc_extractor
from app.data_ingestion.vector_store import vector_store

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

def generate_sample_pdf(file_path: Path):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(file_path), pagesize=letter)
        c.drawString(100, 750, "GLOBAL MASTER SERVICES AGREEMENT & SLA")
        c.drawString(100, 730, "Vendor: Silicon Foundry International (SUP-501)")
        c.drawString(100, 710, "Effective Date: January 1, 2026 | Classification: Confidential")
        c.drawString(100, 680, "Section 4.2: Supply Chain Lead Times & Service Level Agreements")
        c.drawString(100, 660, "- Standard hardware delivery threshold: 48 business hours from fab batch release.")
        c.drawString(100, 640, "- Late Delivery Penalty: 5% liquidated damages per week of delay against order line value.")
        c.drawString(100, 620, "- Critical Failure Threshold: Any delay exceeding 96 hours triggers executive escalation.")
        c.drawString(100, 600, "Section 7.1: Warranty & Substrate Defect Remediation")
        c.drawString(100, 580, "- Vendor warrants High-Bandwidth AI Accelerators (SKU-MOD-101) against substrate defects.")
        c.drawString(100, 560, "- In case of fab raw material shortages, vendor must supply buffer stock within 7 days.")
        c.save()
        print(f"[Seed] Created PDF: {file_path}")
    except Exception as e:
        print(f"[Seed] PDF generation fallback: {e}")
        # Create text fallback
        with open(file_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
            f.write("GLOBAL MASTER SERVICES AGREEMENT & SLA\nVendor: Silicon Foundry International (SUP-501)\nSection 4.2: 48 hour delivery threshold; 5% penalty per week delay.")

def generate_sample_csv(file_path: Path):
    content = """quarter,business_unit,allocated_budget_usd,actual_spend_usd,variance_pct,cost_center_head
Q1-2026,Cloud Data Centers,1800000,1750000,-2.7,Dr. Marcus Vance
Q2-2026,Cloud Data Centers,2000000,2120000,6.0,Dr. Marcus Vance
Q3-2026,Cloud Data Centers,2200000,2490000,13.1,Dr. Marcus Vance
Q3-2026,AI Hardware Accelerators,1500000,1420000,-5.3,Elena Rostova
Q4-2026,Cloud Data Centers,2500000,2680000,7.2,Dr. Marcus Vance
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Seed] Created CSV: {file_path}")

def generate_sample_email(file_path: Path):
    content = """From: logistics-alerts@siliconfoundry.global
To: supplychain-director@enterprise.internal
Subject: URGENT: Fab Batch Delay Notice - High-Bandwidth AI Accelerators (SKU-MOD-101)
Date: 2026-11-12 08:30:00

Dear Enterprise Procurement Team,

Please be advised that fab production line #4 encountered an unanticipated substrate raw material shortage during Q3-Q4 wafer processing.
Deliveries for SKU-MOD-101 (High-Bandwidth AI Accelerator) allocated for the Austin-TX-DC1 facility will experience an operational delay of 112 hours.

In accordance with Section 4.2 of the Master Services Agreement, the liquidated damages penalty of $14,200.00 will be credited directly to your November statement.
Emergency buffer allocation of 40 units is currently en route from our Taipei hub.

Sincerely,
Global Logistics Operations | Silicon Foundry International
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Seed] Created Email: {file_path}")

def generate_sample_confluence(file_path: Path):
    content = """# Confluence SOP: High-Value Customer Credit Review & Order Release
**Space:** Enterprise Finance & Risk (FIN-RISK)
**Version:** 3.4 | **Last Updated:** 2026-10-01

## 1. Credit Limit Policy
Any order exceeding $100,000.00 where the customer's outstanding balance exceeds 80% of their established credit limit must automatically transition to `On Hold - Credit Review`.

## 2. Release Authorization Matrix
- **Tier 1 (Enterprise/Strategic)**: Credit review approval authorized by Senior Financial Analyst or CFO.
- **Tier 2 (Standard)**: Minimum 50% upfront payment wire required before fulfillment release.

## 3. Meridian Retail Global (CUST-1005) Special Terms
Meridian Retail maintains a $1,200,000 credit limit with Net-30 payment terms. As of Q4-2026, their outstanding balance stands at $420,000. Recent order ORD-2026-8805 ($215,000) triggered standard compliance review due to credit utilization spikes.
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Seed] Created Confluence SOP: {file_path}")

def main():
    print("=== [1/3] Seeding Structured Systems (ERP & BigQuery Warehouse) ===")
    erp_connector.seed_initial_erp_data()
    print("ERP Tables Seeded: erp_customers, erp_inventory, erp_orders, erp_order_items, erp_suppliers")

    print("\n=== [2/3] Generating Raw Documents (PDF, CSV, Email, Confluence) ===")
    pdf_path = RAW_DIR / "vendor_sla_contract_silicon_foundry.pdf"
    csv_path = RAW_DIR / "q3_2026_financial_variance_report.csv"
    eml_path = RAW_DIR / "escalation_thread_austin_dc.eml"
    cnf_path = RAW_DIR / "sop_confluence_hardware_procurement.md"

    generate_sample_pdf(pdf_path)
    generate_sample_csv(csv_path)
    generate_sample_email(eml_path)
    generate_sample_confluence(cnf_path)

    print("\n=== [3/3] Ingesting & Creating Unified Semantic Vectors in Pinecone Store ===")
    all_chunks = []

    if pdf_path.exists():
        all_chunks.extend(doc_extractor.extract_pdf(str(pdf_path)))
    if csv_path.exists():
        all_chunks.extend(doc_extractor.extract_spreadsheet(str(csv_path)))
    if eml_path.exists():
        with open(eml_path, "r", encoding="utf-8") as f:
            all_chunks.extend(doc_extractor.extract_email(f.read(), email_id="EML-AUSTIN-801"))
    if cnf_path.exists():
        with open(cnf_path, "r", encoding="utf-8") as f:
            all_chunks.extend(doc_extractor.extract_confluence_page(
                title="SOP: Customer Credit Review & Order Release",
                space="FIN-RISK",
                markdown_content=f.read(),
                page_id="CONF-SOP-901"
            ))

    indexed_count = vector_store.upsert_chunks(all_chunks)
    print(f"Successfully generated and indexed {indexed_count} semantic vector chunks into {vector_store.backend} store!")
    print("\nPlatform data seeding complete! Ready for multi-agent workflows.")

if __name__ == "__main__":
    main()

