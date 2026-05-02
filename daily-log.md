## Day 1 — April 4, 2026
- Set up Python venv, Anthropic SDK, .env, .gitignore, GitHub repo
- Debugged: wrong model name, .env.example exposed real key (learned about GitHub secret scanning)
- WIN: First Claude API call working — Claude answered "What is the meaning of life?"
- Tomorrow: Day 2 — refactor into OOP class with async, add error handling

## Day 2 — April 9, 2026
- Rebuilt quickstart.py as a proper Python class (ClaudeClient)
- Learned: system prompts control Claude's persona and behavior
- Learned: method parameters must be declared — missing `system: str` caused TypeError
- WIN: Same Claude responded as a technical expert AND a 5-year-old using the same method
- Tomorrow: Day 3 — Tool Use (function calling)

## Day 3 — April 13, 2026
- Built tool use script — Claude correctly decided to call get_weather('Manila')
- Learned: tool_use stop_reason means Claude chose to call a function instead of answering
- Learned: tool_input is a dict, access with [] not ()
- Added retry logic with exponential backoff for 529 overload errors
- Blocked: Anthropic servers overloaded (529) — full output test pending
- Tomorrow: rerun tool_use.py to confirm full output, then continue Day 3

## Day 3 — April 14, 2026
- Tool use fully working — Claude calls get_weather() for Manila and Tokyo
- Key insight: stop_reason tells you everything:
  - tool_use = Claude chose to call a function
  - end_turn = Claude answered directly without tools
- Claude correctly skipped the tool for "What is 2+2?" — it knows when NOT to use tools
- Added retry logic for 529 overload errors
- WIN: First real AI decision-making loop working end to end
- Tomorrow: Day 4 — multi-turn conversations + persistent memory

## Day 4 — April 18, 2026
- Built a CLI chatbot that remembers conversations across sessions
- Memory saved to memory.json — persists even after terminal is closed
- Key insight: Claude has zero memory by default — YOU are responsible 
  for passing history back on every API call
- WIN: Claude remembered my name, location, and goals from a previous session
- Tomorrow: Day 5 — Node.js crash course, rewrite Day 1 in JavaScript

## Day 5 — April 20, 2026
- Rebuilt Claude chatbot in JavaScript/Node.js
- Learned: package.json needs "type": "module" for ES import syntax
- Learned: template literals use backticks not regular quotes for ${variables}
- WIN: Same Claude integration now working in both Python AND JavaScript
- Tomorrow: Day 6 — Prompt Engineering deep dive + prompt template library

## Day 6 — April 20, 2026
- Built a 10-template prompt library covering: code review, teaching, summarizing, debugging, email writing, SQL, product management, standup, data extraction, and roast reviewer
- Key insight: system prompts are the most powerful tool in AI engineering — same Claude, completely different behavior
- WIN: Code reviewer caught SQL injection vulnerability automatically
- WIN: Standup bot turned raw bullet points into professional update in seconds
- Tomorrow: Day 7 — review and polish all Week 1 repos, write proper README

## Day 7 - April 21, 2026
- Git polishing

## Day 8 — April 21, 2026 (Concepts)

### What I Learned: Agents vs Chatbots

**Chatbot** — reacts to one message, answers, done.
**Agent** — given a goal, figures out the steps itself and keeps working until complete.

Key difference: a chatbot reacts, an agent acts.

### The ReAct Pattern (Reason + Act)
Every agent loop looks like this:
- REASON: "What do I need to do next?"
- ACT: Call a tool
- REASON: "What did I get back? Is the goal done?"
- ACT: Call another tool OR stop

### 3 Things a Research Agent Needs
1. **Search** — get information from the web
2. **Reason** — read results and decide: enough or need more?
3. **Write** — save the report when done

### Memory Types
| Type | Human equivalent | Built on |
|------|-----------------|----------|
| In-context | What's in your head right now | Day 4 messages array |
| External | Notes in a notebook | Day 4 memory.json |
| Semantic | Searchable knowledge base | Week 3 |

### Architecture

## Day 9 — April 23, 2026
- Built first autonomous research agent
- Claude searched 5 times across 2 iterations — decided on its own when to search more
- Claude called write_report on iteration 3 — decided on its own when it had enough
- Agent produced 700-word report with 8 sources saved to .md file
- Fixed: duckduckgo-search package renamed to ddgs
- Fixed: stop_response typo → stop_reason
- Key insight: the agent loop + system prompt is all you need — no framework required
- WIN: First truly autonomous AI system — goal in, report out
- Tomorrow: Day 10 — structured output + file I/O improvements

## Day 10 — May 1, 2026

### What Was Built
- Upgraded research agent with dual file output: saves both a `.md` report AND a `_summary.json` summary file
- Agent autonomously searched the web, compiled 15 sources, and produced a 2,100-word report in one run

### What Was Learned
- All three layers of tool use must stay in sync: **tool schema → function signature → run_tool dispatcher**
  - If even one is out of sync, Claude sends data your code can't handle and the message chain breaks
- Nested objects in tool schemas confuse Claude — always flatten to top-level fields when possible
- Dead code after `break` silently kills your agent loop — Python won't warn you
- `max_tokens` affects the full conversation context, not just the reply — long searches eat into the budget fast

### Bugs Fixed

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `tool_use ids found without tool_result blocks` (first occurrence) | `write_report` had a nested `summary` object in the schema — Claude produced malformed tool calls | Flattened `summary` fields (`title`, `key_findings`, `sources_count`, `word_count`) to top-level schema properties |
| `cannot use 'dict' as a set element` | Bracket mismatch during schema edit — Python misread `{...}` as a set | Rewrote entire `tools = [...]` block cleanly from scratch |
| `tool_use ids found without tool_result blocks` (second occurrence) | `messages.append({"role": "user", ...})` was placed inside the `else` block **after** `break` — dead code, never executed | Moved `messages.append` to correct position: outside the `for` loop but inside the `elif tool_use` block |
| `Unexpected stop_reason: max_tokens` | `max_tokens=4096` wasn't enough for multi-search context + full report generation | Increased `max_tokens` to `8096` |

### WIN 🏆
First research agent that saves structured output — goal in, `.md` report + `.json` summary out. Fully autonomous, no framework required.

### What's Next
- Day 11 — MCP concepts (read Anthropic MCP docs)
- Day 12 — Build first MCP server

## Day 12 — May 2, 2026

### What Was Built
- First MCP server (`server.py`) exposing two tools via FastMCP:
  - `get_weather` — returns weather data for a given city
  - `search_web` — DuckDuckGo search, reused from Day 9
- Test client (`test_client.py`) to verify Claude reasons about MCP-exposed tools

### What Was Learned
- MCP servers use `stdio` transport — running server.py directly looks like an error but is expected behavior; it needs a client to connect
- `FastMCP` decorator pattern `@mcp.tool()` is cleaner than manually defining tool schemas
- Same tools from Days 3–9 can be lifted into an MCP server with minimal changes
- MCP makes tools external and reusable — any MCP-compatible client can use them without rewriting

### Bugs Fixed
| Bug | Fix |
|-----|-----|
| `Invalid JSON: EOF while parsing` when running `server.py` directly | Not a bug — MCP stdio servers expect a client connection. Run `test_client.py` instead |

### WIN 🏆
Claude autonomously called `get_weather` twice for Manila and Tokyo from a single message — same behavior as Day 3, but now powered by a standalone reusable MCP server.

### What's Next
- Day 13 — MCP + SQLite (connect your MCP server to a real database)

## Day 13 — May 2, 2026

### What Was Built
- MCP server (`server.py`) backed by SQLite with 4 tools:
  - `create_table` — initializes notes table
  - `add_note` — inserts a note with title and content
  - `get_notes` — retrieves all notes ordered by date
  - `search_notes` — keyword search across title and content
- Test client (`test_client.py`) with full agent loop:
  - Claude creates table, adds 3 notes, retrieves all, and searches — from plain English

### What Was Learned
- SQLite is built into Python — no install needed, perfect for local MCP servers
- `conn.row_factory = sqlite3.Row` lets you access columns by name instead of index
- MCP tools are just Python functions — any existing Python code can become an MCP tool
- Claude can chain multiple DB operations in one instruction ("create table AND add 3 notes")

### Bugs Fixed
None — clean run on first attempt. ✅

### WIN 🏆
Claude managed a real SQLite database using plain English — no SQL written by the user.
Full CRUD-like operations through natural language via MCP tools.

### What's Next
- Day 14 — Review + Document all Week 2 work (Days 8–13)