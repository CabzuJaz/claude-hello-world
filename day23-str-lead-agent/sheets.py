import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

CREDENTIALS_FILE = "/Users/jazzminsicat-cabizares/30-Day-Claude-Sprint/claude-hello-world/google_credentials.json"
SHEET_NAME = "STR Leads"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = ["Company", "Website", "Email", "Phone", "LinkedIn", "Location", "Found Via", "Date"]

def get_sheet():
    """Connect to Google Sheets."""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    client = gspread.Client(auth=creds)
    return client.open(SHEET_NAME).sheet1

def ensure_headers():
    """Check if headers exist in row 1 - add them if missing."""
    try:
        sheet = get_sheet()
        first_row = sheet.row_values(1)
        if first_row != HEADERS:
            sheet.insert_row(HEADERS, 1)
            print("[Sheets] Headers added.")
        else:
            print("[Sheets] Headers already exist.")
    except Exception as e:
        print(f"[Sheets] Error checking headers: {e}")

def append_lead(company_name: str, website: str = None, email: str = None,
                phone: str = None, linkedin_url: str = None,
                location: str = None, source: str = None):
    """Append one lead row to Google Sheets - never overwrites headers."""
    try:
        sheet = get_sheet()

        # ✅ Safety check - ensure headers are in row 1 before appending
        first_row = sheet.row_values(1)
        if first_row != HEADERS:
            sheet.insert_row(HEADERS, 1)
            print("[Sheets] Headers were missing - added.")

        row = [
            company_name or "",
            website or "",
            email or "",
            phone or "",
            linkedin_url or "",
            location or "",
            source or "",
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ]
        next_row = len(sheet.get_all_values()) + 1
        sheet.update(f"A{next_row}", [row])
        print(f"[Sheets] Appended: {company_name}")
    except Exception as e:
        print(f"[Sheets] Error appending lead: {e}")

def clear_sheet():
    """Clear all data except headers - for testing only."""
    try:
        sheet = get_sheet()
        # ✅ Delete all rows after row 1 - keeps headers intact
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            sheet.delete_rows(2, len(all_values))
        print("[Sheets] Sheet cleared - headers preserved.")
    except Exception as e:
        print(f"[Sheets] Error clearing sheet: {e}")