import anthropic
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tools = [
    {
        "name": "search_web",
        "description": "Search the web for information on a given topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "write_report",
        "description": "Save the final research report with structured summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
                "title": {"type": "string"},
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "sources_count": {"type": "integer"},
                "word_count": {"type": "integer"}
            },
            "required": ["filename", "content", "title", "key_findings", "sources_count", "word_count"]
        }
    }
]

def search_web(query: str, max_results: int = 5) -> str:
    print(f" [search_web] Searching: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']} - {r['body']}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search error: {e}"
    
def write_report(filename: str, content: str, title: str,
                 key_findings: list, sources_count: int, word_count: int) -> str:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    summary = {
        "title": title,
        "key_findings": key_findings,
        "sources_count": sources_count,
        "word_count": word_count,
        "generated_at": datetime.now().isoformat(),
        "report_file": filename
    }

    json_filename = filename.replace(".md", "_summary.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f" [write_report] Saved: {filename}")
    print(f" [write_report] Saved: {json_filename}")
    return f"Report saved to {filename} and {json_filename}"

def run_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_web":
        return search_web(tool_input["query"], tool_input.get("max_results", 5))
    elif tool_name == "write_report":
        return write_report(
            tool_input["filename"],
            tool_input["content"],
            tool_input["title"],
            tool_input["key_findings"],
            tool_input["sources_count"],
            tool_input["word_count"]
        )
    
    return f"Unknown tool: {tool_name}"

def run_agent(topic: str):
    print(f"\n{'='*50}")
    print(f"Topic: {topic}")
    print(f"{'='*50}\n")

    system_prompt = """You are a research agent. Research the topic thoroughly then write a report.

    Search 2-3 times maximum. Keep search queries short and focused.
    When calling write_report, you MUST include:
    - title: the report title
    - key_findings: list of 3-5 key findings as strings
    - sources_count: number of sources used
    - word_count: approximate word count of the report

    Save the report as a .md file."""

    messages = [
        {"role": "user", "content": f"Research this topic and write a structured report: {topic}"}
    ]

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"--- Iteration {iteration} ---")

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=8096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        print(f"Stop reason: {response.stop_reason}")

        # Always append full assistant response first
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nClaude: {block.text}")
            break
        elif response.stop_reason == "tool_use":
            # Build one tool_result for EVERY tool_use block
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"Claude calls: {block.name}")
                    try:
                        result = run_tool(block.name, block.input)
                    except Exception as e:
                        result = f"Tool error: {str(e)}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
        else:
            # Safety net — stop_reason was something unexpected (e.g. max_tokens)
            print(f"Unexpected stop_reason: {response.stop_reason} — stopping.")
            break        
            # Append ALL tool results in one user message
        messages.append({"role": "user", "content": tool_results})

    print(f"\n{'='*50}")
    print("DONE — check your folder for .md and _summary.json files")
    print(f"{'='*50}")

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    run_agent(topic)