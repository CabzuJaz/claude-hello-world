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