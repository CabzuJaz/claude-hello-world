from mcp.server.fastmcp import FastMCP
import sqlite3
import os

DB_PATH = "notes.db"

mcp = FastMCP("sqlite-notes")

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def create_table() -> str:
    """Create the notes table if it doesn't exist."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    return "Notes table ready."

@mcp.tool()
def add_note(title: str, content: str) -> str:
    """Add a new note to the database."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (title, content)
    )
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return f"Note saved with ID {note_id}."

@mcp.tool()
def get_notes() -> str:
    """Retrieve all notes from the database."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    if not rows:
        return "No notes found."

    formatted = []
    for row in rows:
        formatted.append(f"[{row['id']}] {row['title']}\n{row['content']}\n({row['created_at']})")
    return "\n\n".join(formatted)

@mcp.tool()
def search_notes(keyword: str) -> str:
    """Search notes by keyword in title or content."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, content FROM notes WHERE title LIKE ? OR content LIKE ?",
        (f"%{keyword}%", f"%{keyword}%")
    ).fetchall()
    conn.close()

    if not rows:
        return f"No notes found matching '{keyword}'."

    formatted = []
    for row in rows:
        formatted.append(f"[{row['id']}] {row['title']}: {row['content']}")
    return "\n\n".join(formatted)

if __name__ == "__main__":
    mcp.run()