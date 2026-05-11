from flask import Flask, request, jsonify
import anthropic
import os
from ddgs import DDGS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

tools = [
    {
        "name": "search_web",
        "description": "Search the web for information on a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "write_report",
        "description": "Save the final research report as a markdown file.",
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
            "required": ["filename", "content", "title",
                         "key_findings", "sources_count", "word_count"]
        }
    }
]

# ─────────────────────────────────────────
# TOOL HANDLERS
# ─────────────────────────────────────────

def search_web(query: str, max_results: int = 5) -> str:
    print(f"  [search_web] '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        return "\n\n".join([
            f"{i+1}. {r['title']} - {r['body']}"
            for i, r in enumerate(results)
        ])
    except Exception as e:
        return f"Search error: {e}"

def write_report(filename: str, content: str, title: str,
                 key_findings: list, sources_count: int, word_count: int) -> str:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [write_report] Saved: {filename}")
    return f"Report saved to {filename}"

def run_tool(name: str, tool_input: dict) -> str:
    if name == "search_web":
        return search_web(tool_input["query"], tool_input.get("max_results", 5))
    elif name == "write_report":
        return write_report(
            tool_input["filename"],
            tool_input["content"],
            tool_input["title"],
            tool_input["key_findings"],
            tool_input["sources_count"],
            tool_input["word_count"]
        )
    return f"Unknown tool: {name}"

# ─────────────────────────────────────────
# AGENT LOOP
# ─────────────────────────────────────────

def run_agent(topic: str) -> dict:
    messages = [{"role": "user", "content": f"Research this topic and write a report: {topic}"}]

    system_prompt = """You are a research agent. Search 2-3 times then write a report.
When calling write_report include: title, key_findings (3-5 items),
sources_count, word_count. Save as a .md file."""

    iterations = 0
    report_file = None

    while iterations < 10:
        iterations += 1
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=8096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
            return {
                "status": "done",
                "topic": topic,
                "report_file": report_file,
                "summary": final_text,
                "iterations": iterations
            }

        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    if block.name == "write_report":
                        report_file = block.input.get("filename")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
            messages.append({"role": "user", "content": tool_results})

        else:
            break

    return {"status": "error", "message": "Max iterations reached"}

# ─────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route("/research", methods=["POST"])
def research():
    data = request.get_json()
    topic = data.get("topic")

    if not topic:
        return jsonify({"error": "topic is required"}), 400

    print(f"\n[API] Research request: '{topic}'")
    result = run_agent(topic)
    return jsonify(result)

if __name__ == "__main__":
    print("MCP API Server running at http://localhost:5001")
    app.run(port=5001, debug=True)