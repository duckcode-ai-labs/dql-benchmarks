"""Create a `legacy` schema of 300 unrelated tables in the private Postgres.

    python3 wwi/legacy-schema.py | psql ...

WideWorldImporters fits on screen, so ZLens shows the model every table and its
search is never tested. These tables push the schema past that budget, the way a
real warehouse does. The names are the look-alikes a real warehouse holds: old
extracts, other departments' copies. The tables are empty: nothing here answers
a question, and they only compete with the right tables in search.
"""

DEPARTMENTS = ["finance", "hr", "crm", "marketing", "ops", "legal", "it", "support", "retail", "logistics"]
SUBJECTS = [
    "customer_notes", "order_history", "invoice_archive", "payment_runs", "stock_snapshots",
    "supplier_contacts", "sales_targets", "revenue_forecast", "delivery_routes", "people_directory",
    "campaign_results", "product_catalog_copy", "transaction_audit", "budget_lines", "ticket_events",
    "contract_terms", "city_regions", "vehicle_logs", "price_lists", "employee_reviews",
    "account_balances", "shipment_tracking", "tax_codes", "promotion_calendar", "returns_log",
    "warehouse_moves", "credit_notes", "loyalty_members", "survey_answers", "exchange_rates",
]
COLUMNS = [
    ("id", "bigint"), ("name", "text"), ("description", "text"), ("status", "text"), ("region", "text"),
    ("customer_id", "bigint"), ("order_id", "bigint"), ("amount", "numeric"), ("quantity", "integer"),
    ("owner_id", "bigint"), ("category", "text"), ("created_at", "timestamp"), ("updated_at", "timestamp"),
]

print("DROP SCHEMA IF EXISTS legacy CASCADE;")
print("CREATE SCHEMA legacy;")
for department in DEPARTMENTS:
    for subject in SUBJECTS:
        columns = ", ".join(f"{name} {kind}" for name, kind in COLUMNS)
        print(f"CREATE TABLE legacy.{department}_{subject} ({columns});")
print("GRANT USAGE ON SCHEMA legacy TO wwi_reader;")
print("GRANT SELECT ON ALL TABLES IN SCHEMA legacy TO wwi_reader;")
