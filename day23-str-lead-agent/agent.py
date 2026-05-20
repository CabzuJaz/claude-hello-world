import anthropic
import os
import json
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from database import save_lead, init_db
from sheets import append_lead, ensure_headers

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────

search_tools = [
    {
        "name": "search_web",
        "description": "Search the web for STR property management companies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    }
]

enrich_tools = [
    {
        "name": "fetch_page",
        "description": "Fetch a webpage and extract contact information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch"}
            },
            "required": ["url"]
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
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']}\nURL: {r['href']}\n{r['body']}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search error: {e}"

def fetch_page(url: str) -> str:
    print(f"  [fetch_page] '{url}'")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:1000]
    except Exception as e:
        return f"Fetch error: {e}"

def run_tool(name: str, tool_input: dict) -> str:
    if name == "search_web":
        return search_web(tool_input["query"], tool_input.get("max_results", 5))
    elif name == "fetch_page":
        return fetch_page(tool_input["url"])
    return f"Unknown tool: {name}"

# ─────────────────────────────────────────
# SEARCH AGENT
# ─────────────────────────────────────────

def search_agent(location: str, property_type: str, max_results: int = 5) -> list:
    """Finds STR management companies for a given location."""
    print(f"\n[Search Agent] Location: {location} | Type: {property_type}")

    messages = [{
        "role": "user",
        "content": f"""Search for short-term rental property management companies
in {location} that manage {property_type} properties.

Call search_web once, then return results as a JSON list:
[
  {{
    "company_name": "Company Name",
    "website": "https://example.com",
    "location": "{location}"
  }}
]

Return up to {max_results} companies from the search results.
Return ONLY the JSON list, no extra text."""
    }]

    system = """You are a lead research specialist.
Call search_web ONCE. Then immediately return whatever companies you found as a JSON list.
Do not search again. Do not look for more results.
Return structured JSON data only. Never invent companies."""

    for _ in range(3):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            tools=search_tools,
            messages=messages
        )

        print(f"  [Tokens] in={response.usage.input_tokens} out={response.usage.output_tokens}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    try:
                        text = block.text.strip()
                        start = text.find("[")
                        end = text.rfind("]") + 1
                        if start != -1 and end > start:
                            companies = json.loads(text[start:end])
                            print(f"[Search Agent] Found {len(companies)} companies")
                            return companies
                        else:
                            print("[Search Agent] No JSON array found")
                            return []
                    except Exception as e:
                        print(f"[Search Agent] Parse error: {e}")
                        return []
            print("[Search Agent] No text block found")
            return []

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
            print(f"[Search Agent] Unexpected stop_reason: {response.stop_reason}")
            break

    return []

# ─────────────────────────────────────────
# ENRICH AGENT
# ─────────────────────────────────────────

def enrich_agent(company: dict) -> dict:
    """Visits company website and extracts public contact info + social media."""
    print(f"\n[Enrich Agent] Enriching: {company['company_name']}")

    default_contact = {
        "email": None,
        "phone": None,
        "linkedin_url": None,
        "social_media": None
    }

    messages = [{
        "role": "user",
        "content": f"""Visit the website for {company['company_name']} at {company['website']}
and extract their publicly listed contact information.

Return a JSON object with this exact format:
{{
  "email": "contact@example.com or null",
  "phone": "+1 555 0000 or null",
  "linkedin_url": "https://linkedin.com/company/... or null",
  "social_media": "https://instagram.com/... or null"
}}

For social_media, return the first social media profile found (Instagram preferred,
then Facebook, then Twitter/X). Return the full URL.
Only include information publicly listed on their website.
Return ONLY the JSON object, no extra text."""
    }]

    # ✅ FIX — fetch once, return immediately, no multi-page crawling
    system = """You are a data enrichment specialist.
Call fetch_page ONCE on the main website URL given.
Then immediately return whatever contact info you found as a JSON object.
Do not fetch additional pages. Do not follow links.
Never guess or invent contact details."""

    for _ in range(3):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            tools=enrich_tools,
            messages=messages
        )

        print(f"  [Tokens] in={response.usage.input_tokens} out={response.usage.output_tokens}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    try:
                        text = block.text.strip()
                        start = text.find("{")
                        end = text.rfind("}") + 1
                        if start != -1 and end > start:
                            contact = json.loads(text[start:end])
                            print(f"  Email       : {contact.get('email')}")
                            print(f"  Phone       : {contact.get('phone')}")
                            print(f"  Social Media: {contact.get('social_media')}")
                            return contact
                        else:
                            print("[Enrich Agent] No JSON object found")
                            return default_contact
                    except Exception as e:
                        print(f"[Enrich Agent] Parse error: {e}")
                        return default_contact
            return default_contact

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

    return default_contact

# ─────────────────────────────────────────
# ORCHESTRATOR AGENT
# ─────────────────────────────────────────

def orchestrator_agent(location: str, property_type: str, max_results: int = 5) -> dict:
    """Validates input, runs pipeline, summarizes results. 1 Sonnet call, no tools, no loop."""
    print(f"\n[Orchestrator] Starting — {location} | {property_type} | max {max_results}")

    # Input validation — no API call
    if not location or not location.strip():
        return {"status": "error", "message": "Location is required.", "leads": []}
    if not property_type or not property_type.strip():
        return {"status": "error", "message": "Property type is required.", "leads": []}
    if max_results < 1 or max_results > 10:
        return {"status": "error", "message": "max_results must be between 1 and 10.", "leads": []}

    # Run pipeline
    leads = run_pipeline(location.strip(), property_type.strip(), max_results)

    if not leads:
        return {"status": "done", "message": "No leads found.", "leads": []}

    # Summarize results — 1 Sonnet call, no tools
    leads_text = "\n".join([
        f"- {l.get('company_name')} | {l.get('website')} | "
        f"{l.get('email') or 'no email'} | "
        f"{l.get('phone') or 'no phone'} | "
        f"{l.get('social_media') or 'no social'}"
        for l in leads
    ])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        system="You are a lead research assistant. Write concise pipeline summaries.",
        messages=[{
            "role": "user",
            "content": f"""Summarize these STR leads found in {location} for {property_type} properties in 2-3 sentences.
Note how many had contact info vs none.

{leads_text}"""
        }]
    )

    print(f"  [Orchestrator Tokens] in={response.usage.input_tokens} out={response.usage.output_tokens}")

    summary = response.content[0].text if response.content else "Pipeline complete."
    print(f"\n[Orchestrator] Summary: {summary}")

    return {
        "status": "done",
        "location": location,
        "property_type": property_type,
        "leads_found": len(leads),
        "summary": summary,
        "leads": leads
    }

# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────

def run_pipeline(location: str, property_type: str, max_results: int = 5) -> list:
    """Full pipeline: search → enrich → save. Saves all leads, warns if no email."""
    print(f"\n{'='*50}")
    print(f"STR Lead Agent Starting")
    print(f"Location: {location} | Type: {property_type}")
    print(f"{'='*50}")

    init_db()
    ensure_headers()

    companies = search_agent(location, property_type, max_results)

    if not companies:
        print("[Pipeline] No companies found.")
        return []

    saved_leads = []
    no_email_count = 0

    for company in companies:
        contact = enrich_agent(company)

        # ✅ FIX — warn but save all leads regardless of email
        if not contact.get("email"):
            print(f"  [Pipeline] Warning: {company['company_name']} — no email found, saving anyway")
            no_email_count += 1

        lead = {**company, **contact}

        try:
            save_lead(
                company_name=lead.get("company_name"),
                website=lead.get("website"),
                email=lead.get("email"),
                phone=lead.get("phone"),
                linkedin_url=lead.get("linkedin_url"),
                social_media=lead.get("social_media"),
                location=lead.get("location"),
                source="DuckDuckGo search"
            )
        except Exception as e:
            print(f"[Pipeline] DB error — lead NOT saved to SQLite: {e}")

        try:
            append_lead(
                company_name=lead.get("company_name"),
                website=lead.get("website"),
                email=lead.get("email"),
                phone=lead.get("phone"),
                linkedin_url=lead.get("linkedin_url"),
                social_media=lead.get("social_media"),
                location=lead.get("location"),
                source="DuckDuckGo search"
            )
        except Exception as e:
            print(f"[Pipeline] Sheets error — lead NOT saved to Sheets: {e}")

        saved_leads.append(lead)

    print(f"\n{'='*50}")
    print(f"Done — {len(saved_leads)} leads saved | {no_email_count} without email")
    print(f"{'='*50}")
    return saved_leads


if __name__ == "__main__":
    location = input("Enter location: ")
    property_type = input("Enter property type (e.g. vacation rental): ")
    max_results = int(input("Max results (1-10): "))
    result = orchestrator_agent(location, property_type, max_results)
    print(f"\nStatus  : {result['status']}")
    print(f"Found   : {result.get('leads_found', 0)} leads")
    print(f"Summary : {result.get('summary', '')}")