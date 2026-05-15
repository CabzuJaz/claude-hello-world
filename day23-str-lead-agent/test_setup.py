from database import init_db, save_lead, get_all_leads, clear_leads
from sheets import append_lead, clear_sheet

print("Testing database...")
init_db()
clear_leads()

save_lead(
    company_name="Sydney STR Management",
    website="https://sydneystr.com.au",
    email="hello@sydneystr.com.au",
    phone="+61 2 1234 5678",
    location="Sydney, Australia",
    source="test"
)

leads = get_all_leads()
print(f"Leads in DB: {len(leads)}")
print(f"First lead: {leads[0]['company_name']}")

print("\nTesting Google Sheets...")
clear_sheet()
append_lead(
    company_name="Sydney STR Management",
    website="https://sydneystr.com.au",
    email="hello@sydneystr.com.au",
    location="Sydney, Australia",
    source="test"
)

print("\nAll tests passed!")