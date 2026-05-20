import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

def init_db():
    """Archive existing leads table and create a fresh one on every run."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Check if leads table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        exists = cursor.fetchone()

        if exists:
            # Archive with today's date
            archive_name = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute(f"ALTER TABLE leads RENAME TO {archive_name}")
            print(f"[DB] Archived existing table as '{archive_name}'")

        # Create fresh leads table with social_media column
        cursor.execute("""
            CREATE TABLE leads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                website     TEXT,
                email       TEXT,
                phone       TEXT,
                linkedin_url TEXT,
                social_media TEXT,
                location    TEXT,
                source      TEXT,
                created_at  TEXT
            )
        """)

        conn.commit()
        print("[DB] Fresh leads table created.")
    finally:
        conn.close()

def save_lead(
    company_name: str,
    website: str = None,
    email: str = None,
    phone: str = None,
    linkedin_url: str = None,
    social_media: str = None,
    location: str = None,
    source: str = None
):
    """Insert a lead — skips if company_name + location already exists."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Deduplicate by company_name + location
        cursor.execute(
            "SELECT id FROM leads WHERE company_name = ? AND location = ?",
            (company_name, location)
        )
        if cursor.fetchone():
            print(f"[DB] Duplicate skipped: {company_name} in {location}")
            return

        cursor.execute("""
            INSERT INTO leads
                (company_name, website, email, phone, linkedin_url, social_media, location, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_name,
            website,
            email,
            phone,
            linkedin_url,
            social_media,
            location,
            source,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        print(f"[DB] Saved: {company_name}")
    except Exception as e:
        print(f"[DB] Save failed for {company_name}: {e}")
        raise
    finally:
        conn.close()

def get_all_leads() -> list:
    """Return all leads as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()