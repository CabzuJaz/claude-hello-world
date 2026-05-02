# Day 13 — MCP + SQLite

MCP server backed by a real SQLite database. Claude manages notes using plain English.

## Tools Exposed
| Tool | Description |
|------|-------------|
| `create_table` | Initializes the notes table |
| `add_note` | Inserts a note with title and content |
| `get_notes` | Retrieves all notes |
| `search_notes` | Keyword search across title and content |

## How to Run
```powershell
venv\Scripts\activate
cd day13-mcp-sqlite
python test_client.py
```

## Key Insight
SQLite is built into Python — no install needed.
Claude can chain multiple DB operations from one plain English instruction.