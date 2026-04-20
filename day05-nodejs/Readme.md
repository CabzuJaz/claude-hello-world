# Day 05 — Claude Chatbot in JavaScript (Node.js)

The same Claude chatbot from Day 04 — rebuilt in JavaScript to demonstrate bilingual ability.

## What it does
- Connects to Claude API using the official `@anthropic-ai/sdk` npm package
- Maintains conversation history within a session
- Uses `async/await` and ES module syntax
- Reads API key from `.env` using `dotenv`

## Setup
```bash
npm install
```

Create a `.env` file:
```
ANTHROPIC_API_KEY=your-key-here
```

## Run it
```bash
node chatbot.js
```

## Example Output
```
Claude JS Chatbot - type 'quit' to exit

You: testing
Claude: Hello! I'm here and ready to help. What would you like to test?

You: quit
Goodbye!
```

## Python vs JavaScript Comparison

| Concept | Python | JavaScript |
|---------|--------|------------|
| Import | `import anthropic` | `import Anthropic from '@anthropic-ai/sdk'` |
| Async | `async def` | `async function` |
| Env vars | `os.getenv()` | `process.env` |
| Package file | `requirements.txt` | `package.json` |

## What I Learned
- The Anthropic SDK works nearly identically in both languages
- `"type": "module"` in package.json is required for ES import syntax
- Template literals in JS use backticks: `` `Hello ${name}` ``
- Knowing both Python and JS makes you a stronger AI engineering candidate