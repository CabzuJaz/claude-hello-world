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
