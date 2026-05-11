# Claude AI Engineering Sprint

30-day sprint building real Claude AI systems from scratch — one working project per day.

Built by [@CabzuJaz](https://github.com/CabzuJaz) · Philippines 🇵🇭 · [Daily Log](./daily-log.md)

---

## What I Built

- Autonomous AI agents that search the web, reason, and write reports
- MCP servers exposing reusable tools to any MCP-compatible client
- Multi-agent pipelines with orchestrator + specialized subagents
- AI email triage workflow running in n8n using Claude Haiku
- Flask API bridging n8n workflows to a Claude research agent
- Real-time weather agent using live external API data
- Stateful chatbot with persistent memory across sessions
- 10-template prompt library for code review, SQL, debugging, and more

---

## Progress

| Day | Project | Concept | Status |
|-----|---------|---------|--------|
| 01 | [First API Call](./day01/) | Anthropic SDK setup | ✅ |
| 02 | [OOP ClaudeClient](./claude_client.py) | Python classes, system prompts | ✅ |
| 03 | [Tool Use](./day03-tool-use/) | Function calling, tool loops | ✅ |
| 04 | [Memory Chatbot](./day04-memory/) | Persistent conversation history | ✅ |
| 05 | [JS Chatbot](./day05-nodejs/) | Node.js, same concept different language | ✅ |
| 06 | [Prompt Library](./day06-prompt-engineering/) | System prompts, prompt engineering | ✅ |
| 07 | GitHub Polish | READMEs, topics, repo structure | ✅ |
| 08 | Agent Architecture | ReAct pattern, memory types (study) | ✅ |
| 09 | [Research Agent v1](./day09-research-agent/) | Autonomous agent loop, DuckDuckGo | ✅ |
| 10 | [Structured Output](./day10-file-output/) | .md report + .json summary from one prompt | ✅ |
| 11 | MCP Concepts | MCP protocol, stdio transport (study) | ✅ |
| 12 | [First MCP Server](./day12-mcp-server/) | FastMCP, reusable tool server | ✅ |
| 13 | [MCP + SQLite](./day13-mcp-sqlite/) | Claude managing a real database | ✅ |
| 14 | Review + Document | READMEs, GitHub topics polish | ✅ |
| 15 | [n8n Setup](./day15-n8n/) | Visual workflow pipeline | ✅ |
| 16 | [AI Email Triage](./day16-email-triage/) | Claude Haiku classifying emails in n8n | ✅ |
| 17 | Multi-Agent Concepts | Orchestrator, subagents, patterns (study) | ✅ |
| 18 | [Multi-Agent Pipeline](./day18-multi-agent/) | Hierarchical orchestrator + search + writer | ✅ |
| 19 | [External API Integration](./day19-external-api/) | Live weather data via OpenWeatherMap | ✅ |
| 20 | [Claude + n8n + MCP](./day20-n8n-mcp/) | Flask API bridging n8n to Claude agent | ✅ |
| 21 | Review + Loom Video | Sprint showcase, portfolio polish | ✅ |
| 22 | Design Capstone | Capstone planning | 🔜 |
| 23 | Design Capstone cont. | | 🔜 |
| 24 | Build Core | | 🔜 |
| 25 | Build Core cont. | | 🔜 |
| 26 | UI + Activity Log | | 🔜 |
| 27 | UI + Activity Log cont. | | 🔜 |
| 28 | Security + Config | | 🔜 |
| 29 | Final Polish | | 🔜 |
| 30 | Ship It 🚀 | | 🔜 |

---

## Tech Stack

| Category | Tools |
|----------|-------|
| **Languages** | Python 3.11+, JavaScript (Node.js v24) |
| **AI** | Anthropic Claude API (Sonnet, Haiku) |
| **Frameworks** | FastMCP, Flask, n8n |
| **Databases** | SQLite |
| **Automation** | n8n, DuckDuckGo Search (ddgs) |
| **External APIs** | OpenWeatherMap |
| **Dev Tools** | Git, GitHub, VS Code, PowerShell |

---

## Key Technical Lessons

- Claude has zero memory by default — you pass full history back on every API call
- `stop_reason: tool_use` means Claude chose to call a function — always append assistant response before tool results
- Flatten nested objects in tool schemas — Claude chokes on nested `input_schema`
- MCP servers use stdio transport — running directly looks like an error, test via a client
- n8n + Anthropic API: build request body in a Code node, never pass extra keys to the API
- Different models for different jobs: Haiku for fast/cheap tasks, Sonnet for quality output
- Dead code after `break` silently kills agent loops — Python won't warn you
- The agent loop + system prompt is all you need — no framework required

---

## Setup

```bash
git clone https://github.com/CabzuJaz/claude-hello-world.git
cd claude-hello-world
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Add your API keys to a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENWEATHER_API_KEY=your_key_here
```

---

## Sprint Philosophy

> One working system per day. No slide decks. No architecture-only phases.
> The code is the proof.

21 days in. 9 days to go. 🚀
