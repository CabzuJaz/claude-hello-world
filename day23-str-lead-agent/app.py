from flask import Flask, jsonify, request, render_template_string
from database import init_db, get_all_leads
from agent import orchestrator_agent
from datetime import datetime

app = Flask(__name__)

# ─────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>STR Lead Agent</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:       #0d0d0d;
    --surface:  #151515;
    --border:   #222;
    --accent:   #c8f135;
    --muted:    #555;
    --text:     #e8e8e8;
    --subtext:  #888;
    --danger:   #ff5f5f;
    --radius:   6px;
    --mono:     'DM Mono', monospace;
    --sans:     'DM Sans', sans-serif;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    min-height: 100vh;
    padding: 48px 24px;
  }

  .wrap { max-width: 960px; margin: 0 auto; }

  /* ── Header ── */
  .header { margin-bottom: 40px; }
  .header h1 {
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.5px;
    color: var(--accent);
    font-family: var(--mono);
  }
  .header p { color: var(--subtext); margin-top: 6px; font-size: 13px; }

  /* ── Form card ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 24px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 12px;
    align-items: end;
  }

  .field label {
    display: block;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--subtext);
    margin-bottom: 6px;
    font-family: var(--mono);
  }

  input[type="text"],
  input[type="number"] {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    font-family: var(--sans);
    font-size: 13px;
    padding: 10px 12px;
    outline: none;
    transition: border-color .15s;
  }
  input:focus { border-color: var(--accent); }

  .btn {
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: var(--radius);
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 500;
    padding: 10px 20px;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity .15s;
    height: 40px;
  }
  .btn:hover { opacity: .85; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }

  /* ── Status bar ── */
  .status-bar {
    display: none;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 16px;
    font-family: var(--mono);
    font-size: 12px;
    color: var(--subtext);
  }
  .status-bar.visible { display: flex; }
  .status-bar.error { border-color: var(--danger); color: var(--danger); }
  .status-bar.success { border-color: var(--accent); color: var(--accent); }

  .spinner {
    width: 14px; height: 14px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .7s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Stats row ── */
  .stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }
  .stat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
  }
  .stat-value {
    font-family: var(--mono);
    font-size: 28px;
    font-weight: 500;
    color: var(--accent);
  }
  .stat-label {
    font-size: 11px;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-top: 4px;
  }

  /* ── Table ── */
  .table-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
  }
  .table-title {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: .08em;
  }
  .refresh-btn {
    background: none;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--subtext);
    font-family: var(--mono);
    font-size: 11px;
    padding: 4px 10px;
    cursor: pointer;
    transition: border-color .15s, color .15s;
  }
  .refresh-btn:hover { border-color: var(--accent); color: var(--accent); }

  table { width: 100%; border-collapse: collapse; }

  thead th {
    padding: 10px 14px;
    text-align: left;
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    background: var(--bg);
  }

  tbody tr {
    border-bottom: 1px solid var(--border);
    transition: background .1s;
  }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: rgba(200,241,53,.03); }

  tbody td {
    padding: 11px 14px;
    font-size: 13px;
    vertical-align: top;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .tag {
    display: inline-block;
    font-family: var(--mono);
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 3px;
    background: rgba(200,241,53,.1);
    color: var(--accent);
  }
  .tag.none {
    background: rgba(255,255,255,.04);
    color: var(--muted);
  }

  a { color: var(--accent); text-decoration: none; font-family: var(--mono); font-size: 11px; }
  a:hover { text-decoration: underline; }

  .empty {
    padding: 48px;
    text-align: center;
    color: var(--muted);
    font-family: var(--mono);
    font-size: 12px;
  }

  /* ── Summary box ── */
  .summary-box {
    display: none;
    background: rgba(200,241,53,.05);
    border: 1px solid rgba(200,241,53,.2);
    border-radius: var(--radius);
    padding: 14px 18px;
    font-size: 13px;
    color: var(--text);
    margin-bottom: 20px;
    line-height: 1.6;
  }
  .summary-box.visible { display: block; }
  .summary-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 6px;
  }
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div class="header">
    <h1>STR_LEAD_AGENT</h1>
    <p>Find short-term rental property management companies by location.</p>
  </div>

  <!-- Search form -->
  <div class="card">
    <div class="form-grid">
      <div class="field">
        <label>Location</label>
        <input type="text" id="location" placeholder="e.g. Gold Coast, Australia" />
      </div>
      <div class="field">
        <label>Property Type</label>
        <input type="text" id="property_type" placeholder="e.g. vacation rental" />
      </div>
      <div class="field">
        <label>Max</label>
        <input type="number" id="max_results" value="5" min="1" max="10" style="width:70px" />
      </div>
    </div>
    <button class="btn" id="search-btn" onclick="startSearch()" style="margin-top:16px">
      Run Agent
    </button>
  </div>

  <!-- Status bar -->
  <div class="status-bar" id="status-bar">
    <div class="spinner" id="spinner"></div>
    <span id="status-text">Searching...</span>
  </div>

  <!-- Summary -->
  <div class="summary-box" id="summary-box">
    <div class="summary-label">Agent Summary</div>
    <span id="summary-text"></span>
  </div>

  <!-- Stats -->
  <div class="stats" id="stats" style="display:none">
    <div class="stat">
      <div class="stat-value" id="stat-total">0</div>
      <div class="stat-label">Total Leads</div>
    </div>
    <div class="stat">
      <div class="stat-value" id="stat-email">0</div>
      <div class="stat-label">With Email</div>
    </div>
    <div class="stat">
      <div class="stat-value" id="stat-social">0</div>
      <div class="stat-label">With Social</div>
    </div>
  </div>

  <!-- Results table -->
  <div class="table-wrap">
    <div class="table-header">
      <span class="table-title">Leads</span>
      <button class="refresh-btn" onclick="loadLeads()">↻ Refresh</button>
    </div>
    <table>
      <thead>
        <tr>
          <th>Company</th>
          <th>Website</th>
          <th>Email</th>
          <th>Phone</th>
          <th>Social</th>
          <th>Location</th>
        </tr>
      </thead>
      <tbody id="results-body">
        <tr><td colspan="6" class="empty">No leads yet — run the agent above.</td></tr>
      </tbody>
    </table>
  </div>

</div>

<script>
  function setStatus(msg, state = 'loading') {
    const bar = document.getElementById('status-bar');
    const spinner = document.getElementById('spinner');
    const text = document.getElementById('status-text');
    bar.className = 'status-bar visible';
    if (state === 'error')   bar.classList.add('error');
    if (state === 'success') bar.classList.add('success');
    spinner.style.display = state === 'loading' ? 'block' : 'none';
    text.innerText = msg;
  }

  function hideStatus() {
    document.getElementById('status-bar').className = 'status-bar';
  }

  async function startSearch() {
    const location     = document.getElementById('location').value.trim();
    const property_type = document.getElementById('property_type').value.trim();
    const max_results  = parseInt(document.getElementById('max_results').value) || 5;

    if (!location)      { alert('Please enter a location'); return; }
    if (!property_type) { alert('Please enter a property type'); return; }

    const btn = document.getElementById('search-btn');
    btn.disabled = true;
    btn.innerText = 'Running...';

    document.getElementById('summary-box').className = 'summary-box';
    setStatus(`Searching for ${property_type} companies in ${location}...`);

    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location, property_type, max_results })
      });

      const data = await res.json();

      if (data.error) {
        setStatus(data.error, 'error');
      } else {
        setStatus(`Done — ${data.leads_found} leads saved.`, 'success');

        if (data.summary) {
          document.getElementById('summary-text').innerText = data.summary;
          document.getElementById('summary-box').className = 'summary-box visible';
        }

        loadLeads();
      }
    } catch (err) {
      setStatus('Request failed — check the terminal for errors.', 'error');
    } finally {
      btn.disabled = false;
      btn.innerText = 'Run Agent';
    }
  }

  async function loadLeads() {
    const res = await fetch('/api/leads');
    const leads = await res.json();
    const tbody = document.getElementById('results-body');

    if (!leads.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty">No leads yet — run the agent above.</td></tr>';
      document.getElementById('stats').style.display = 'none';
      return;
    }

    // Stats
    const withEmail  = leads.filter(l => l.email).length;
    const withSocial = leads.filter(l => l.social_media).length;
    document.getElementById('stat-total').innerText  = leads.length;
    document.getElementById('stat-email').innerText  = withEmail;
    document.getElementById('stat-social').innerText = withSocial;
    document.getElementById('stats').style.display   = 'grid';

    // Rows
    tbody.innerHTML = leads.map(l => `
      <tr>
        <td title="${l.company_name}">${l.company_name}</td>
        <td>${l.website ? `<a href="${l.website}" target="_blank">↗ visit</a>` : '<span class="tag none">—</span>'}</td>
        <td>${l.email    ? `<span class="tag">${l.email}</span>`    : '<span class="tag none">—</span>'}</td>
        <td>${l.phone    ? `<span class="tag">${l.phone}</span>`    : '<span class="tag none">—</span>'}</td>
        <td>${l.social_media ? `<a href="${l.social_media}" target="_blank">↗ social</a>` : '<span class="tag none">—</span>'}</td>
        <td title="${l.location}">${l.location}</td>
      </tr>
    `).join('');
  }

  // Load on page init
  loadLeads();
</script>
</body>
</html>
"""

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/search", methods=["POST"])
def search():
    data          = request.get_json()
    location      = data.get("location", "").strip()
    property_type = data.get("property_type", "short-term rental").strip()
    max_results   = int(data.get("max_results", 5))

    if not location:
        return jsonify({"error": "location is required"}), 400

    # Cap max_results — token safety
    max_results = min(max_results, 10)

    print(f"[API] Search: {location} | {property_type} | max {max_results}")

    result = orchestrator_agent(location, property_type, max_results)

    if result["status"] == "error":
        return jsonify({"error": result["message"]}), 400

    return jsonify({
        "status":      result["status"],
        "leads_found": result.get("leads_found", 0),
        "summary":     result.get("summary", ""),
        "message":     f"Done — {result.get('leads_found', 0)} leads saved."
    })


@app.route("/api/leads", methods=["GET"])
def leads():
    return jsonify(get_all_leads())


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    init_db()
    print("STR Lead Agent running at http://localhost:5002")
    app.run(port=5002, debug=True)