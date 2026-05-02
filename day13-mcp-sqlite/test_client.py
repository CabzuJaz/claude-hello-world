import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tools = [
    {
        "name": "create_table",
        "description": "Create the notes table if it doesn't exist.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "add_note",
        "description": "Add a new note to the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "get_notes",
        "description": "Retrieve all notes from the database.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "search_notes",
        "description": "Search notes by keyword in title or content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"}
            },
            "required": ["keyword"]
        }
    }
]

def run_tool(name, tool_input):
    """Execute the actual SQLite tool."""
    import sqlite3
    DB_PATH = "notes.db"

    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    if name == "create_table":
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

    elif name == "add_note":
        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (tool_input["title"], tool_input["content"])
        )
        conn.commit()
        note_id = cursor.lastrowid
        conn.close()
        return f"Note saved with ID {note_id}."

    elif name == "get_notes":
        conn = get_db()
        rows = conn.execute(
            "SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        if not rows:
            return "No notes found."
        return "\n\n".join([f"[{r['id']}] {r['title']}\n{r['content']}" for r in rows])

    elif name == "search_notes":
        conn = get_db()
        rows = conn.execute(
            "SELECT id, title, content FROM notes WHERE title LIKE ? OR content LIKE ?",
            (f"%{tool_input['keyword']}%", f"%{tool_input['keyword']}%")
        ).fetchall()
        conn.close()
        if not rows:
            return f"No notes found matching '{tool_input['keyword']}'."
        return "\n\n".join([f"[{r['id']}] {r['title']}: {r['content']}" for r in rows])

    return f"Unknown tool: {name}"

def run_agent(user_message: str):
    print(f"\nUser: {user_message}")
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            tools=tools,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"Claude: {block.text}")
            break
        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Calling: {block.name}({block.input})")
                    result = run_tool(block.name, block.input)
                    print(f"  ← Result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            print(f"Unexpected stop_reason: {response.stop_reason}")
            break

if __name__ == "__main__":
    # Test sequence — Claude manages the DB in plain English
    run_agent("Create the notes table, then add 3 notes about Python, MCP, and SQLite.")
    run_agent("Show me all my notes.")
    run_agent("Search my notes for anything about MCP.")