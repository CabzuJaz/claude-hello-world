# Day 06 — Prompt Engineering & Template Library

A library of 10 reusable system prompts that transform Claude into specialized AI personas.

## What it does
- Defines 10 production-ready prompt templates
- Demonstrates how system prompts completely change Claude's behavior
- Shows structured output formatting using XML tags, bullet points, and JSON
- Includes a demo runner that tests 4 templates automatically

## Run it
```bash
python prompts.py
```

## Prompt Templates

| Template | What it does |
|----------|-------------|
| `code_reviewer` | Reviews code for bugs, security issues, and rates quality 1-10 |
| `summarizer` | TL;DR + bullet takeaways + action items under 150 words |
| `teacher` | Explains concepts to beginners using analogies + practice exercise |
| `data_extractor` | Extracts structured data and returns clean JSON only |
| `email_writer` | Writes professional emails under 150 words with subject line |
| `debugger` | Explains errors in plain English and provides fixed code |
| `product_manager` | Structures ideas as Problem / Solution / Risks / Metrics |
| `sql_expert` | Writes optimized, commented PostgreSQL queries |
| `standup_bot` | Formats bullet points into Yesterday / Today / Blockers |
| `roast_reviewer` | Gordon Ramsay-style brutal but constructive code review |

## How to Use a Template
```python
from prompts import use_template

result = use_template("code_reviewer", your_code_here)
print(result)
```

## Example Output — Code Reviewer
```
## <bugs>
1. SQL Injection Vulnerability — string formatting in query
2. No database connection cleanup
3. No error handling

## <security>
CRITICAL: f"SELECT * FROM users WHERE id = {id}" is injectable

## <rating>
2/10 — Requires immediate refactoring
```

## What I Learned
- System prompts are the most powerful tool in AI engineering
- The same Claude model produces completely different output with different system prompts
- Structured output (XML tags, JSON, markdown) makes AI responses parseable by code
- A prompt template library is a reusable asset across all future projects