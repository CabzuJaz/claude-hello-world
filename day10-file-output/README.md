# Day 10 — Structured File Output

Upgraded research agent that saves both a Markdown report and a JSON summary.

## What It Does
- Searches the web autonomously (2–3 queries)
- Saves a `.md` report with full research content
- Saves a `_summary.json` with title, key findings, source count, word count

## How to Run
```powershell
venv\Scripts\activate
cd day10-file-output
python structured_agent.py
```

## Key Fix
Tool schema must be fully flat — nested objects in `input_schema`
cause Claude to produce malformed tool calls.

## Output Files
| File | Description |
|------|-------------|
| `<topic>.md` | Full research report |
| `<topic>_summary.json` | Structured metadata summary |