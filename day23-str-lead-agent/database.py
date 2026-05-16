import sqlite3
from datetime import datetime
import os

# ✅ Save directly to day23-str-lead-agent folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

def init_db():
    """
    Check if leads table exists.
    If yes — rename it to leads_YYYYMMDD then create fresh leads table.
    If no — create fresh leads table.
    """
    conn = sqlite3.connect(DB_PATH)

    try:
        # Check if leads table exists
        existing = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='leads'
        """).fetchone()

        if existing:
            # Archive with date only
            timestamp = datetime.now().strftime("%Y%m%d")
            archive_name = f"leads_{timestamp}"

            # Check if archive name already exists — add suffix if it does
            archive_exists = conn.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{archive_name}'
            """).fetchone()

            if archive_exists:
                archive_name = f"{archive_name}_v2"

            conn.execute(f"ALTER TABLE leads RENAME TO {archive_name}")
            conn.commit()
            print(f"[DB] Existing table archived as: {archive_name}")

        else:
            print("[DB] No existing table found — creating fresh.")

        # ✅ Always create new leads table after archiving
        conn.execute("""
            CREATE TABLE leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                website TEXT,
                email TEXT,
                phone TEXT,
                linkedin_url TEXT,
                location TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print(f"[DB] New leads table created at: {DB_PATH}")

    except Exception as e:
        print(f"[DB] Error during init: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_lead(company_name: str, website: str = None, email: str = None,
              phone: str = None, linkedin_url: str = None,
              location: str = None, source: str = None) -> int:
    """Save a lead to SQLite. Returns the new lead ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Deduplicate — don't save same company twice
        existing = conn.execute(
            "SELECT id FROM leads WHERE company_name = ? AND location = ?",
            (company_name, location)
        ).fetchone()

        if existing:
            print(f"[DB] Skipped duplicate: {company_name}")
            return existing["id"]

        cursor = conn.execute("""
            INSERT INTO leads (company_name, website, email, phone,
                              linkedin_url, location, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_name, website, email, phone, linkedin_url, location, source))

        conn.commit()
        lead_id = cursor.lastrowid
        print(f"[DB] Saved: {company_name} (ID: {lead_id})")
        return lead_id

    except Exception as e:
        print(f"[DB] Error saving lead: {e}")
        conn.rollback()
        return -1
    finally:
        conn.close()

def get_all_leads() -> list:
    """Fetch all leads from current leads table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[DB] Error fetching leads: {e}")
        return []
    finally:
        conn.close()

def get_archived_tables() -> list:
    """List all archived lead tables."""
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'leads_%'
            ORDER BY name DESC
        """).fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"[DB] Error fetching archives: {e}")
        return []
    finally:
        conn.close()

def clear_leads():
    """Clear all leads from current table — for testing only."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM leads")
        conn.commit()
        print("[DB] All leads cleared.")
    except Exception as e:
        print(f"[DB] Error clearing leads: {e}")
    finally:
        conn.close()