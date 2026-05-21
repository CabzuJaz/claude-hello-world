import anthropic
import os
import re
import html
import json
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from database import save_lead, init_db
from sheets import append_lead, ensure_headers
from config import (
    ANTHROPIC_API_KEY,
    REQUEST_TIMEOUT,
    MAX_RESULTS_LIMIT,
    validate_config
)

load_dotenv()

# ✅ Validate config on import — fails fast with clear message
validate_config()

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────
# REGEX PATTERNS
# ─────────────────────────────────────────

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(r'\+?[\d][\d\s\-().]{6,14}[\d]')

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
# LINK EXTRACTORS
# ─────────────────────────────────────────

SOCIAL_PATTERNS = [
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "tiktok.com",
    "pinterest.com"
]

CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contact/",
    "/contact-us/",
    "/get-in-touch",
    "/about",
    "/about-us"
]

def extract_social_links(soup) -> list:
    """Pull social media URLs from <a href> tags before any stripping."""
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if any(pattern in href for pattern in SOCIAL_PATTERNS):
            if href not in found:
                found.append(href)
    return found

def extract_contact_links(soup) -> tuple:
    """Pull emails and phones from mailto:/tel: href attributes before any stripping."""
    emails = []
    phones = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if email and email not in emails:
                emails.append(email)
        elif href.startswith("tel:"):
            phone = href.replace("tel:", "").strip()
            if phone and phone not in phones:
                phones.append(phone)
    return emails, phones

def _scrape_contact_soup(s) -> str:
    """Shared helper — scrape contact info from a BeautifulSoup object."""
    contact_emails, contact_phones = extract_contact_links(s)
    contact_socials = extract_social_links(s)

    for tag in s(["script", "style"]):
        tag.decompose()

    raw  = s.get_text(separator=" ", strip=True)
    full = html.unescape(raw)

    regex_emails = EMAIL_REGEX.findall(full)
    regex_phones = PHONE_REGEX.findall(full)

    all_emails = list(dict.fromkeys(contact_emails + regex_emails))
    all_phones = list(dict.fromkeys(contact_phones + regex_phones))

    text = full[:800]

    if all_emails:
        text += "\n\nEMAILS FOUND: " + " | ".join(all_emails)
    if all_phones:
        text += "\n\nPHONES FOUND: " + " | ".join(all_phones)
    if contact_socials:
        text += "\n\nSOCIAL LINKS FOUND: " + " | ".join(contact_socials)

    return text

def fetch_contact_page(base_url: str, soup) -> str:
    """
    Find and fetch the contact page.
    Strategy 1 — follow link found on page.
    Strategy 2 — fallback: try common contact paths directly.
    """
    req_headers = {"User-Agent": "Mozilla/5.0"}

    # ── Strategy 1: follow link found on homepage ──
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        href_lower = href.lower()

        if any(path in href_lower for path in CONTACT_PATHS):
            if href.startswith("http"):
                contact_url = href
            else:
                base = base_url.rstrip("/")
                contact_url = base + ("" if href.startswith("/") else "/") + href

            print(f"  [fetch_contact_page] {contact_url}")
            try:
                r = requests.get(contact_url, headers=req_headers, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    s = BeautifulSoup(r.text, "html.parser")
                    return _scrape_contact_soup(s)
            except Exception as e:
                print(f"  [fetch_contact_page] Error: {e}")

    # ── Strategy 2: fallback — try common paths directly ──
    base = base_url.rstrip("/").split("?")[0]
    for path in ["/contact-us/", "/contact-us", "/contact/", "/contact"]:
        try:
            contact_url = base + path
            r = requests.get(contact_url, headers=req_headers, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200 and len(r.text) > 500:
                print(f"  [fetch_contact_page] Fallback hit: {contact_url}")
                s = BeautifulSoup(r.text, "html.parser")
                return _scrape_contact_soup(s)
        except Exception:
            continue

    return ""

# ─────────────────────────────────────────
# TOOL HANDLERS
# ─────────────────────────────────────────

def search_web(query: str, max_results: int = 5) -> str:
    print(f"  [search_web] '{query}'")
    # ✅ Cap max_results to limit
    max_results = min(max_results, MAX_RESULTS_LIMIT)
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
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(response.text, "html.parser")

        social_links   = extract_social_links(soup)
        emails, phones = extract_contact_links(soup)

        for tag in soup(["script", "style"]):
            tag.decompose()

        raw_text  = soup.get_text(separator=" ", strip=True)
        full_text = html.unescape(raw_text)

        regex_emails = EMAIL_REGEX.findall(full_text)
        regex_phones = PHONE_REGEX.findall(full_text)

        all_emails = list(dict.fromkeys(emails + regex_emails))
        all_phones = list(dict.fromkeys(phones + regex_phones))

        main_text    = full_text[:800]
        contact_text = fetch_contact_page(url, soup)

        combined = main_text

        if contact_text:
            combined += "\n\nCONTACT PAGE:\n" + contact_text
        if all_emails:
            combined += "\n\nEMAILS FOUND: " + " | ".join(all_emails)
        if all_phones:
            combined += "\n\nPHONES FOUND: " + " | ".join(all_phones)
        if social_links:
            combined += "\n\nSOCIAL LINKS FOUND: " + " | ".join(social_links)

        return combined

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
  "social_media": "https://instagram.com/... or https://facebook.com/... or null"
}}

The page content will include these sections — use them directly:
- EMAILS FOUND: use the first email listed
- PHONES FOUND: use the first phone listed
- CONTACT PAGE: additional contact info from their contact page
- SOCIAL LINKS FOUND: use for social_media (prefer Instagram, then Facebook, then Twitter/X, then TikTok)

Only include information publicly listed on their website.
Return ONLY the JSON object, no extra text."""
    }]

    system = """You are a data enrichment specialist.
Call fetch_page ONCE on the main website URL given.
The result includes homepage text, contact page content, and extracted links.
Return whatever contact info you found as a JSON object immediately.
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

    # ✅ Input validation
    if not location or not location.strip():
        return {"status": "error", "message": "Location is required.", "leads": []}
    if not property_type or not property_type.strip():
        return {"status": "error", "message": "Property type is required.", "leads": []}
    if max_results < 1 or max_results > MAX_RESULTS_LIMIT:
        return {"status": "error", "message": f"max_results must be between 1 and {MAX_RESULTS_LIMIT}.", "leads": []}

    leads = run_pipeline(location.strip(), property_type.strip(), max_results)

    if not leads:
        return {"status": "done", "message": "No leads found.", "leads": []}

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

    saved_leads    = []
    no_email_count = 0

    for company in companies:
        contact = enrich_agent(company)

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
    location      = input("Enter location: ")
    property_type = input("Enter property type (e.g. vacation rental): ")
    max_results   = int(input(f"Max results (1-{MAX_RESULTS_LIMIT}): "))
    result = orchestrator_agent(location, property_type, max_results)
    print(f"\nStatus  : {result['status']}")
    print(f"Found   : {result.get('leads_found', 0)} leads")
    print(f"Summary : {result.get('summary', '')}")