## Day 16 — May 4, 2026

### What Was Built
- n8n workflow: Manual Trigger → Fake Emails → Build Body → Claude API → Parse Response
- Claude Haiku categorizes emails into: urgent, follow-up, newsletter, spam
- Each email gets: category, priority, summary, and action

### What Was Learned
- n8n's JSON body field does NOT evaluate {{ }} inside nested strings reliably — 
  use a Code node to build the request body instead
- The Anthropic API rejects unknown top-level fields — only send what the API expects
  (model, max_tokens, messages) — pass email context inside the prompt string, not as extra keys
- Claude sometimes wraps JSON in markdown code fences (` ```json `) — 
  always strip them before parsing
- n8n processes items one at a time through the workflow chain — 
  4 emails = 4 separate executions per node

### Bugs Fixed
| Bug | Fix |
|-----|-----|
| `Authorization failed - invalid x-api-key` | API key was missing or had extra spaces in header |
| `{{ $json.from }}` not evaluated in JSON body | Moved body construction to a Code node using template literals |
| `from: Extra inputs are not permitted` | Removed `from`/`subject` as top-level keys — kept them inside prompt string only |
| `Could not parse` in parse node | Added `.replace(/\`\`\`json\n?/g, '')` to strip markdown code fences from Claude's response |

### WIN 🏆
Claude autonomously triaged 4 emails — correctly flagged production outage as 
urgent/high, newsletter as low, recruiter as spam, PR review as follow-up/medium.
Full AI pipeline running inside a visual workflow tool.
