# STR Lead Research Agent

An AI agent that finds short-term rental property management companies by location, enriches them with public contact info, and saves results to SQLite and Google Sheets — with a live web frontend and real-time activity log.

**Part of:** [30-Day Claude AI Engineering Sprint](../README.md)  
**Built:** Days 22–30  
**Stack:** Python 3.11, Flask, Claude Haiku + Sonnet, DuckDuckGo, SQLite, Google Sheets, SSE

---

## What It Does

```
User enters location + property type
            ↓
Orchestrator validates input
            ↓
Search Agent — DuckDuckGo → JSON list of companies
            ↓
Enrich Agent (per company)
  ├── fetch homepage
  ├── extract mailto: and tel: hrefs
  ├── regex scan full text (catches plain text emails/phones)
  ├── html.unescape() (catches &#64; encoded emails)
  ├── fetch contact page (link follow + fallback paths)
  └── extract social links from <a href>
            ↓
save_lead() → SQLite (dedup by company + location)
append_lead() → Google Sheets
            ↓
Orchestrator summarizes results (1 Sonnet call)
            ↓
Frontend updates live via SSE
```

---

## Features

- Real-time activity log — every agent step streams to the browser via SSE
- Multi-strategy contact extraction — `mailto:`, `tel:`, regex, HTML entity decoding, contact page fallback
- SQLite deduplication — never saves the same company + location twice
- Google Sheets sync — live lead sheet, headers protected
- Agent summary — Sonnet writes a 2-3 sentence summary after each run
- Stats row — total leads, with email, with social
- Token logging — every API call prints input/output token count

---

## Architecture

```
app.py          Flask API + HTML frontend + SSE stream
agent.py        Orchestrator + Search Agent + Enrich Agent
database.py     SQLite — init, save, deduplicate
sheets.py       Google Sheets sync via gspread
config.py       Single source of truth for all env config
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/CabzuJaz/claude-hello-world
cd claude-hello-world
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp day23-str-lead-agent/.env.example day23-str-lead-agent/.env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=your_key_here
GOOGLE_CREDENTIALS_FILE=/absolute/path/to/google_credentials.json
SHEET_NAME=STR Leads
FLASK_PORT=5002
FLASK_DEBUG=false
```

### 3. Google Sheets setup

1. Create a Google Cloud project
2. Enable Google Sheets API + Google Drive API
3. Create a service account → download credentials JSON
4. Share your Google Sheet with the service account email
5. Set `GOOGLE_CREDENTIALS_FILE` in `.env`

### 4. Run

```bash
cd day23-str-lead-agent
python app.py
```

Open `http://localhost:5002`

---

## Usage

| Field | Example |
|-------|---------|
| Location | Gold Coast, Australia |
| Property Type | vacation rental |
| Max Results | 5 (max 10) |

Hit **Run Agent** — watch the activity log stream in real time.

---

## Contact Extraction — How It Works

The enrich agent runs four extraction strategies on every site:

| Strategy | Catches |
|----------|---------|
| `mailto:` href scan | `<a href="mailto:info@example.com">` |
| `tel:` href scan | `<a href="tel:+61400000000">` |
| Regex on full page text | Plain text emails and phones in footer |
| `html.unescape()` | `&#64;` encoded emails (anti-scraper technique) |
| Contact page — link follow | Site has `/contact` link in nav |
| Contact page — fallback | Tries `/contact`, `/contact-us`, `/contact/` directly |
| Social `<a href>` scan | Instagram, Facebook, LinkedIn, Twitter/X, TikTok, Pinterest |

---

## Known Limitations

| Limitation | Reason | Workaround |
|------------|--------|------------|
| JS-rendered sites (React/Next.js) | `requests` fetches HTML before JS executes | Playwright (not implemented) |
| Facebook contact info | FB blocks scraping — returns login wall | Save FB URL, check manually |
| DuckDuckGo rate limits | Too many searches too fast | Built-in `for _ in range(3)` cap |

---

## Token Usage

Estimated per run (5 leads, Haiku):

| Agent | Calls | Input | Output |
|-------|-------|-------|--------|
| Search agent | 2 | ~1,100 | ~150 |
| Enrich × 5 | 10 | ~5,000 | ~400 |
| Orchestrator summary | 1 | ~200 | ~100 |
| **Total** | **13** | **~6,300** | **~650** |

**Cost: ~$0.007 per run** at Haiku pricing.

---

## Key Lessons

- `while True` + LLM tool loops = runaway costs. Always use `for _ in range(N):`
- Emails are often in `href="mailto:"` not page text — extract before stripping HTML
- `html.unescape()` is required — many sites encode `@` as `&#64;` to block scrapers
- `requests.get()` never sees JS-rendered content — confirmed with `False False` test
- `gspread.append_row()` writes horizontally when table range is ambiguous — use `sheet.update(f"A{n}", [row])`
- Config in one place (`config.py`) beats scattered `os.getenv()` calls everywhere

---

## File Reference

```
day23-str-lead-agent/
├── agent.py          Orchestrator + Search + Enrich agents
├── app.py            Flask API + SSE + HTML frontend
├── database.py       SQLite — archive on init, dedup save
├── sheets.py         Google Sheets sync
├── config.py         Environment config + startup validation
├── .env.example      Environment variable template
├── .env              Your local config (not committed)
├── leads.db          SQLite database (not committed)
└── test_setup.py     DB + Sheets connection tests
```