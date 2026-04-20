# Day 03 — Tool Use / Function Calling

Claude decides when to call your Python functions based on the user's message.

## What it does
- Defines a `get_weather()` mock function as a tool
- Claude autonomously decides to call it when asked about weather
- Skips the tool entirely for unrelated questions
- Includes retry logic for API overload errors (529)

## Key Concept
```
stop_reason: tool_use  → Claude wants to call a function
stop_reason: end_turn  → Claude answered directly, no tool needed
```

## Run it
```bash
python tool_use.py
```

## Example Output
```
User: What's the weather like in Manila?
Stop reason: tool_use
Claude wants to call: get_weather {'city': 'Manila'}
Tool result: 32°C, humid, partly cloudy
Claude: The current weather in Manila is 32°C, humid, and partly cloudy.

User: What is 2+2?
Stop reason: end_turn
Claude: 2 + 2 = 4
```

## What I Learned
- Tool use is the foundation of every AI agent
- Claude makes intelligent decisions about WHEN to use tools
- The two-step API call pattern: first call to decide, second call to respond with result