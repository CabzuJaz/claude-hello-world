from json import tool

import anthropic
import os
import json
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Tools Claude can use ---

tools = [
    {
        "name": "search_web",
        "description": "Search the web for information on a  topic. Returns a list of results with titles, URLS, and snippets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to results to return (default 5)",
                    "default": 5
                
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "write_report",
        "description": "Save the final research as a markdown file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to save the report as (e.g. report.md)"
                },
                "content": {
                    "type": "string",
                    "description": "The full markdown content of the report"
                }
            },
            "required": ["filename", "content"]
        }
    }
]

# --- Your actual Python functions ---
def search_web(query: str, max_results: int = 5) -> str:
    print(f" [search_web] Searching: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        formatted = []

        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']}\n URL: {r['href']}\n {r['body']}")
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"Search error: {e}"

def write_report(filename: str, content: str) -> str:
    print(f" [write_report] Saving report to '{filename}'")
    with open (filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Report saved to '{filename}'"

# --- Tool dispatcher ---
def run_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_web":
        return search_web(
                tool_input["query"],
                tool_input.get("max_results", 5)
        )
    elif tool_name == "write_report":
        return write_report(
            tool_input["filename"],
            tool_input["content"]
        )
    else:
        return f"Unknown tool: {tool_name}"
    
# --- The agent loop ---
def run_research_agent(topic:str):
    print(f"\n{'='*50}")
    print(f"RESEARCH AGENT STARTING")
    print(f"Topic: {topic}")
    print(f"{'='*50}\n")

    system_prompt = """You are a research agent. Your job is to research a topic thoroughly and write a report.
    
        You have access to two tools:
        1. search-web - use this to search for information. Search multiple times with different queries to get comprehensive coverage.
        2. write_report - use this ONLY when you have enough information to write a complete report.

        Your process:

        - Search at least 2-3 times with different queries.
        - Gather enough information to write a 300-500 word report.
        - Write a well-structured markdown report with: title, summary, key findings, and sources.
        - Save the report using write_report tool.

        Do not stop until the reportt is saved.
    """

    messages = [
        {"role": "user", "content": f"Research this topic and write a report: {topic}"}
    ]

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"--- Iteration {iteration} ---")

        response = client.messages.create(
            model = "claude-sonnet-4-5",
            max_tokens = 4096,
            system = system_prompt,
            tools=tools,
            messages=messages
        )

        print(f"Stop reason: {response.stop_reason}")

        #Add Claude's response to history
        messages.append({
            "role": "assistant",
            "content": response.content,
        })

        # If Claude is done
        if response.stop_reason == "end_turn":
            print("\nAgent finished.")
            # Print any final text
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nClaude: {block.text}")
            break

        # If Claude wants to use tools
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"Claude calls: {block.name}")
                    result = run_tool(block.name, block.input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            # Send tool results back to Claude
            messages.append({
                "role": "user",
                "content": tool_results
            })
    print(f"\n{'='*50}")
    print("AGENT COMPLETE")
    print(f"{'='*50}")

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    run_research_agent(topic)