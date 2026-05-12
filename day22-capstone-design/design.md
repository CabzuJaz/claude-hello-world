# Capstone — AI Lead Research Agent for STR Property Managers
*Date:* May 13, 2026

## What It Does
An AI agent that takes a location and property type from the user,
searches for short-term rental property management companies in that
area, finds their publicly listed contact information, cross-references
their social media presence, and saves structured leads to Google Sheets.

## Who It's For
- Real estate agencies looking for STR management partnerships
- B2B service providers targeting property managers
- Anyone doing legitimate outreach to STR management companies

## Data Sources (all public, no ToS violations)
- Google / DuckDuckGo search results
- Company websites (publicly listed contact pages)
- LinkedIn public profiles
- Google Maps / Google Business listings

## System Architecture
User (location + property type)
        ↓
Flask API
        ↓
Orchestrator Agent (Claude Sonnet)
        ↓
┌──────────────────────────────────────┐
│  Search Agent     │   Enrich Agent   │
│  DuckDuckGo       │  company website │
│  Google Maps      │  LinkedIn search │
└────────┬──────────┴────────┬──────────┘
         │                   │
    Writer Agent
    (structures + deduplicates)
         ↓
   Google Sheets API
        ↓
   Live spreadsheet

## Tech Stack
- Frontend  : Simple HTML form (Flask served)
- Backend   : Flask API
- Database  : SQLite (local cache of found leads)
- AI        : Claude Sonnet (orchestrator + writer)
             Claude Haiku (search + enrich agents)
- Search    : DuckDuckGo (ddgs)
- Output    : Google Sheets API (gspread)

## Tools Exposed to Claude
- search_web(query) — DuckDuckGo search
- fetch_page(url) — read a company contact page
- search_linkedin(name, location) — find public profile
- save_lead(data) — write to SQLite + Google Sheets

## Pages / Screens
1. Input form — location, property type, max results
2. Live progress — agent steps shown in real time
3. Results table — all leads found with status badges

## Data Schema
leads table:
- id
- company_name
- website
- email (publicly listed only)
- phone (publicly listed only)
- linkedin_url
- location
- source (where it was found)
- created_at

## API Endpoints
- POST /api/search — start agent with location + type
- GET  /api/leads  — fetch all saved leads
- GET  /api/status — check agent progress

## Google Sheets Output Columns
Company | Website | Email | Phone | LinkedIn | Location | Found Via | Date

## Build Timeline
| Day | Task |
|-----|------|
| 22  | Design + Google Sheets API setup |
| 23  | Scaffold Flask + SQLite + gspread |
| 24  | Build search agent + enrich agent |
| 25  | Build orchestrator + writer agent |
| 26  | Frontend UI — form + results table |
| 27  | Activity log + real-time progress |
| 28  | Security + config + error handling |
| 29  | Final polish + README |
| 30  | Ship + Loom demo 🚀 |

## Ship Checklist
- [ ] Flask API running
- [ ] Search agent finding real companies
- [ ] Enrich agent finding public contact info
- [ ] SQLite caching leads locally
- [ ] Google Sheets syncing in real time
- [ ] Frontend form working
- [ ] Results table displaying correctly
- [ ] Activity log showing agent steps
- [ ] Error handling for dead links
- [ ] README written
- [ ] Loom recorded

## Ethical Guidelines
- Only collect publicly listed contact information
- Never scrape behind login walls
- Deduplicate — never save same company twice
- Rate limit — don't hammer websites
- Include data source column — full transparency