# Claude AI Engineering Sprint — Week 1

30-day sprint building real Claude AI projects from scratch.
Built by [@CabzuJaz](https://github.com/CabzuJaz) | Philippines 🇵🇭

## Projects

| Day | Project | Key Concept |
|-----|---------|-------------|
| 01 | [First API Call](./day01/) | Anthropic SDK, streaming |
| 02 | [OOP ClaudeClient](./claude_client.py) | Python classes, error handling |
| 03 | [Tool Use](./day03-tool-use/) | Function calling, tool loops |
| 04 | [Memory Chatbot](./day04-memory/) | Persistent conversation history |
| 05 | [JS Chatbot](./day05-nodejs/) | Node.js, same concept different language |
| 06 | [Prompt Library](./day06-prompt-engineering/) | System prompts, prompt engineering |

## Tech Stack
- Python 3.11+
- Node.js v24
- Anthropic SDK (Python + JS)
- python-dotenv

## Setup
```bash
git clone https://github.com/CabzuJaz/claude-hello-world.git
cd claude-hello-world
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Key Learnings This Week
- Claude has no memory by default — you pass history manually every call
- `stop_reason: tool_use` means Claude chose to call a function
- System prompts control everything about Claude's behavior
- The gap between Python dev and AI engineer is smaller than it looks