# Day 04 — Stateful Chatbot with Persistent Memory

A CLI chatbot that remembers your conversation — even after you close the terminal.

## What it does
- Saves full conversation history to `memory.json` after every message
- Loads previous conversation on startup so Claude remembers past sessions
- Supports `clear` command to reset memory and start fresh
- Uses a system prompt to encourage Claude to reference past context

## Run it
```bash
python chatbot.py
```

## Commands
| Command | Action |
|---------|--------|
| Any message | Chat normally |
| `clear` | Wipe memory and start fresh |
| `quit` | Exit and save conversation |

## Example Output
```
Loaded 6 messages from memory.

You: What do you remember about me?

Claude: From our conversation, I remember:
1. Your name is Jazzmin Sicat-Cabizares
2. You are currently learning AI Engineering
3. You are based in the Philippines
```

## How Memory Works
```python
# Every message gets appended to history
history.append({"role": "user", "content": user_input})

# History is passed to Claude on every API call
response = client.messages.create(messages=history)

# Response gets saved back to history and written to JSON
history.append({"role": "assistant", "content": reply})
save_memory(history)
```

## What I Learned
- Claude has zero built-in memory — you are responsible for passing history
- File-based memory (JSON) is the simplest form of agent persistence
- This same pattern scales to databases, vector stores, and semantic memory