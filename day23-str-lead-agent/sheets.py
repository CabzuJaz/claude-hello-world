import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import requests

CREDENTIALS_FILE = "/Users/jazzminsicat-cabizares/30-Day-Claude-Sprint/claude-hello-world/google_credentials.json"
SHEET_NAME = "STR Leads"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    """Connect to Google Sheets."""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    client = gspread.Client(auth=creds)
    return client.open(SHEET_NAME).sheet1

def append_lead(company_name: str, website: str = None, email: str = None, phone: str = None, linked_url: str = None,
                location: str = None, source: str = None):
    """Append a lead to the Google Sheet."""
    try:
        sheet = get_sheet()
        row = [
            company_name or "",
            website or "",
            email or "",
            phone or "",
            linked_url or "",
            location or "",
            source or "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet.append_row(row)
        print(f"[Sheets] Appended: {company_name}")
    except Exception as e:
        print(f"[Sheets] Error appending lead: {e}")

def clear_sheet():
    """Clear all data except headers - for testing only."""
    try:
        sheet = get_sheet()
        sheet.resize(1)
        print("[Sheets] Sheets cleared.")
    except Exception as e:
        print(f"[Sheets] Error clearing sheet: {e}")