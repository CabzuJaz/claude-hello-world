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
        "content": f"""Search for {max_results} short-term rental property management
companies in {location} that manage {property_type} properties.

Return results as a JSON list:
[
  {{
    "company_name": "Company Name",
    "website": "https://example.com",
    "location": "{location}"
  }}
]

Include ALL companies found in search results.
Return ONLY the JSON list, no extra text."""
    }]

    system = """You are a lead research specialist. Search for STR property
management companies and return structured JSON data only.
Never invent companies — only return real ones found in search results."""

    for _ in range(5):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system,
            tools=search_tools,
            messages=messages
        )

        #To check token usage for debugging
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
    """Visits company website and extracts public contact info."""
    print(f"\n[Enrich Agent] Enriching: {company['company_name']}")

    # ✅ FIX 2 — default contact defined upfront
    default_contact = {"email": None, "phone": None, "linkedin_url": None}

    messages = [{
        "role": "user",
        "content": f"""Visit the website for {company['company_name']} at {company['website']}
and extract their publicly listed contact information.

Return a JSON object with this exact format:
{{
  "email": "contact@example.com or null",
  "phone": "+1 555 0000 or null",
  "linkedin_url": "https://linkedin.com/company/... or null"
}}

Only include information that is publicly listed on their website.
Return ONLY the JSON object, no extra text."""
    }]

    system = """You are a data enrichment specialist. Visit company websites
and extract only publicly listed contact information.
Never guess or invent contact details."""

    for _ in range(5):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            tools=enrich_tools,
            messages=messages
        )

        #To check token usage for debugging
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
                            print(f"  Email: {contact.get('email')}")
                            print(f"  Phone: {contact.get('phone')}")
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
# MAIN PIPELINE
# ─────────────────────────────────────────
def run_pipeline(location: str, property_type: str, max_results: int = 5) -> list:
    """Full pipeline: search → enrich → save."""
    print(f"\n{'='*50}")
    print(f"STR Lead Agent Starting")
    print(f"Location: {location} | Type: {property_type}")
    print(f"{'='*50}")

    # Always initialize DB first before anything else
    init_db()
    ensure_headers()

    companies = search_agent(location, property_type, max_results)

    if not companies:
        print("[Pipeline] No companies found.")
        return []

    saved_leads = []
    for company in companies:
        contact = enrich_agent(company)
        lead = {**company, **contact}

        save_lead(
            company_name=lead.get("company_name"),
            website=lead.get("website"),
            email=lead.get("email"),
            phone=lead.get("phone"),
            linkedin_url=lead.get("linkedin_url"),
            location=lead.get("location"),
            source="DuckDuckGo search"
        )

        append_lead(
            company_name=lead.get("company_name"),
            website=lead.get("website"),
            email=lead.get("email"),
            phone=lead.get("phone"),
            linkedin_url=lead.get("linkedin_url"),
            location=lead.get("location"),
            source="DuckDuckGo search"
        )

        saved_leads.append(lead)

    print(f"\n{'='*50}")
    print(f"Done — {len(saved_leads)} leads saved")
    print(f"{'='*50}")
    return saved_leads

if __name__ == "__main__":
    location = input("Enter location: ")
    property_type = input("Enter property type (e.g. vacation rental): ")
    max_results = int(input("Max results (e.g. 5): "))
    run_pipeline(location, property_type, max_results)