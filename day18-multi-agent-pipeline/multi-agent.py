import anthropic
import os
from ddgs import DDGS
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

search_tool = {
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
}

def search_web(query: str, max_results: int = 5) -> str:
    print(f"    [search_web] '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        return "\n\n".join([f"{i+1}. {r['title']} - {r['body']}" for i, r in enumerate(results)])
    except Exception as e:
        return f"Search error: {e}"

def run_tool(name, tool_input):
    if name == "search_web":
        return search_web(tool_input["query"], tool_input.get("max_results", 5))
    return f"Unknown tool: {name}"

# ─────────────────────────────────────────
# SUBAGENT — Search Agent
# ─────────────────────────────────────────

def search_agent(subtopic: str) -> str:
    """Specialized agent — searches and summarizes one subtopic."""
    print(f"\n  [Search Agent] Researching: '{subtopic}'")

    messages = [{"role": "user", "content": f"Research this subtopic thoroughly and summarize your findings in 200-300 words: {subtopic}"}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system="You are a research specialist. Search the web and summarize findings concisely.",
            tools=[search_tool],
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            break
        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Search agent returned no results."

# ─────────────────────────────────────────
# SUBAGENT — Writer Agent
# ─────────────────────────────────────────

def writer_agent(topic: str, research_findings: list[str]) -> str:
    """Specialized agent — combines research into a final report."""
    print(f"\n  [Writer Agent] Writing report on: '{topic}'")

    combined = "\n\n---\n\n".join([f"Finding {i+1}:\n{f}" for i, f in enumerate(research_findings)])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system="You are a professional technical writer. Write clear, well-structured reports.",
        messages=[{
            "role": "user",
            "content": f"""Write a comprehensive research report on: {topic}

Use these research findings as your source material:

{combined}

Structure the report with:
- Executive Summary
- Key Findings (3-5 points)
- Detailed Analysis
- Conclusion

Aim for 500-700 words."""
        }]
    )

    return response.content[0].text

# ─────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────

def orchestrator(topic: str) -> str:
    """Orchestrator — breaks topic into subtopics, delegates to subagents."""
    print(f"\n{'='*50}")
    print(f"[Orchestrator] Topic: {topic}")
    print(f"{'='*50}")

    # Step 1 — Orchestrator plans subtopics
    print("\n[Orchestrator] Planning subtopics...")
    plan_response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        system="You are a research orchestrator. Break topics into 2-3 focused subtopics for parallel research. Respond with ONLY a numbered list of subtopics, nothing else.",
        messages=[{"role": "user", "content": f"Break this topic into 2-3 focused research subtopics: {topic}"}]
    )

    plan_text = plan_response.content[0].text
    print(f"\n[Orchestrator] Subtopics:\n{plan_text}")

    # Parse subtopics
    subtopics = []
    for line in plan_text.strip().split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            # Remove numbering/bullets
            cleaned = line.lstrip("0123456789.-) ").strip()
            if cleaned:
                subtopics.append(cleaned)

    if not subtopics:
        subtopics = [topic]

    # Step 2 — Delegate to search agents (sequential for now)
    print(f"\n[Orchestrator] Delegating to {len(subtopics)} search agents...")
    findings = []
    for subtopic in subtopics:
        result = search_agent(subtopic)
        findings.append(result)

    # Step 3 — Delegate to writer agent
    print(f"\n[Orchestrator] Sending {len(findings)} findings to writer agent...")
    report = writer_agent(topic, findings)

    # Step 4 — Save report
    filename = topic.lower().replace(" ", "_")[:40] + "_report.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n")
        f.write(report)

    print(f"\n[Orchestrator] Report saved to: {filename}")
    return filename

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    topic = input("Enter research topic: ")
    filename = orchestrator(topic)

    print(f"\n{'='*50}")
    print(f"DONE — report saved to day18-multi-agent/{filename}")
    print(f"{'='*50}")