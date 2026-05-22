# 30-Day Claude AI Engineering Sprint

A self-directed sprint building progressively complex AI systems with the Anthropic Claude API — from a single API call to a full multi-agent pipeline with a live web frontend.

**Built by:** Jazzmin Sicat-Cabizares  
**GitHub:** [github.com/CabzuJaz](https://github.com/CabzuJaz)  
**Stack:** Python 3.11, Flask, SQLite, Claude API, n8n, MCP, Google Sheets

---

## What Was Built

### Foundation (Days 1–7)
| Day | What |
|-----|------|
| 1 | First Claude API call |
| 2 | OOP `ClaudeClient` class |
| 3 | Tool use / function calling |
| 4 | Stateful chatbot with memory |
| 5 | JavaScript chatbot (Node.js) |
| 6 | 10-template prompt library |
| 7 | GitHub polish + READMEs |

### Agents & MCP (Days 8–14)
| Day | What |
|-----|------|
| 8 | Agent architecture (study) |
| 9 | Autonomous research agent v1 |
| 10 | Structured file output (.md + .json) |
| 11 | MCP concepts (study) |
| 12 | First MCP server (FastMCP) |
| 13 | MCP + SQLite |
| 14 | Review + document |

### Integrations (Days 15–21)
| Day | What |
|-----|------|
| 15 | n8n setup |
| 16 | AI email triage in n8n (Claude Haiku) |
| 17 | Multi-agent concepts (study) |
| 18 | Multi-agent pipeline (orchestrator + subagents) |
| 19 | External API integration (OpenWeatherMap) |
| 20 | Claude + n8n + MCP together (Flask API bridge) |
| 21 | Review + Loom video + README update |

### Capstone — STR Lead Research Agent (Days 22–30)
| Day | What |
|-----|------|
| 22 | Capstone design |
| 23 | Scaffold Flask + SQLite + Google Sheets |
| 24 | Search agent + enrich agent |
| 25 | Orchestrator agent |
| 26 | Frontend UI (form + results table) |
| 27 | Activity log + real-time SSE progress |
| 28 | Security + config + error handling |
| 29 | Final polish + README |
| 30 | Ship + Loom demo |

---

## Key Technical Patterns Learned

**Tool use loop pattern**
```python
for _ in range(3):               # never while True
    response = client.messages.create(...)
    print(f"[Tokens] in={response.usage.input_tokens} out={response.usage.output_tokens}")
    if response.stop_reason == "end_turn":
        # parse and return
    elif response.stop_reason == "tool_use":
        # handle tool, append result
```

**JSON extraction (handles Claude preamble)**
```python
start = text.find("[")
end   = text.rfind("]") + 1
data  = json.loads(text[start:end])
```

**Always close DB connections**
```python
try:
    cursor.execute(...)
    conn.commit()
finally:
    conn.close()
```

---

## Bugs Worth Documenting

| Bug | Fix |
|-----|-----|
| `while True` loop hit 50k TPM rate limit — cost $2+ | Replaced with `for _ in range(3):` |
| `gspread.append_row()` wrote data horizontally | Replaced with `sheet.update(f"A{next_row}", [row])` |
| Mac smart punctuation inserted em dash `—` in Python | Fixed with `sed -i '' 's/—/-/g' filename.py` |
| Email in `&#64;` encoded footer not found by regex | Added `html.unescape()` before regex scan |
| Contact page not found when homepage has no nav link | Added fallback — tries `/contact`, `/contact-us` directly |
| JS-rendered sites return empty HTML via `requests` | Documented as known limitation — Playwright needed |

---

## Tech Stack

```
Python 3.11          Claude Haiku 4.5 (search + enrich)
Flask                Claude Sonnet 4.5 (orchestrator)
SQLite               DuckDuckGo (ddgs)
gspread              BeautifulSoup
Google Sheets API    n8n
FastMCP              Server-Sent Events (SSE)
```

---

## Capstone

→ See [`day23-str-lead-agent/README.md`](day23-str-lead-agent/README.md)

---

## How to Run Any Day

```bash
git clone https://github.com/CabzuJaz/claude-hello-world
cd claude-hello-world
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp day23-str-lead-agent/.env.example day23-str-lead-agent/.env
# fill in .env with your API keys
python day23-str-lead-agent/app.py
```