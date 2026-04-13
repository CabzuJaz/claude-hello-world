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
