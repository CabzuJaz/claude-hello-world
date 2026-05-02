# Day 12 — First MCP Server

A standalone MCP server exposing reusable tools via FastMCP.

## Tools Exposed
| Tool | Description |
|------|-------------|
| `get_weather` | Returns weather for a given city |
| `search_web` | DuckDuckGo web search |

## How to Run
```powershell
venv\Scripts\activate
cd day12-mcp-server

# Test Claude reasoning about your tools
python test_client.py
```

## Key Insight
Running `server.py` directly shows a JSON error — this is expected.
MCP stdio servers need a client to connect. Always test via `test_client.py`.