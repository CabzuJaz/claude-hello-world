# Day 9 — Autonomous Research Agent

An AI agent that autonomously searches the web and writes a research report.

## What It Does
- Searches DuckDuckGo 2–5 times based on what it needs
- Decides on its own when it has enough information
- Writes a structured `.md` report with sources

## How to Run
```powershell
venv\Scripts\activate
cd day09-research-agent
python research_agent.py
```

## Key Concepts
- ReAct pattern: Reason → Act → Reason → Act → Done
- `stop_reason == "tool_use"` means Claude chose to call a function
- `stop_reason == "end_turn"` means Claude is done