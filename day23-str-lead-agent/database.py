import sqlite3
from datetime import datetime

DB_PATH = "leads.db"

def init_db():
    """Create leads table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
                 company_name TEXT NOT NULL,
                 website TEXT,
                 email TEXT,
                 phone TEXT,
                 linked_url TEXT,
                 location TEXT,
                 source TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("[DB] Database initialized.")

def save_lead(company_name: str, website: str = None, email: str = None, phone: str = None, linked_url: str = None,
              location: str = None, source: str = None) -> int:
    """Save a lead to SQLite. Returns the new lead ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Deduplicate - don't save company twice
    existing = conn.execute(
        "SELECT id FROM leads WHERE company_name = ? AND location = ?", (company_name, location)).fetchone()

    if existing:
        conn.close()
        print(f"[DB] Skipped duplicate: {company_name}")
        return existing["id"]
    
    cursor = conn.execute("""
        INSERT INTO leads (company_name,
        website, email, phone, linked_url, location, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_name, website, email, phone, linked_url, location, source))
    
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    print(f"[DB] Saved: {company_name} (ID: {lead_id})")
    return lead_id

def get_all_leads() -> list:
    """Fetch all leads from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM leads ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_leads():
    """Clear all leads - for testing only."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM leads")
    conn.commit()
    conn.close()
    print("[DB] All leads cleared.")