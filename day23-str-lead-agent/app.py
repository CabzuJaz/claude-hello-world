from flask import Flask, jsonify, request, render_template_string, Response, stream_with_context
from database import init_db, get_all_leads
from agent import orchestrator_agent
from datetime import datetime
import queue
import threading
import sys

app = Flask(__name__)

# ─────────────────────────────────────────
# GLOBAL STATE — single-user sprint tool
# ─────────────────────────────────────────

_log_queue   = queue.Queue()
_result      = {}
_is_running  = False


class StreamCapture:
    """Captures print() output → log queue + terminal."""
    def __init__(self, q):
        self.q        = q
        self._stdout  = sys.__stdout__
    def write(self, text):
        self._stdout.write(text)
        if text.strip():
            self.q.put(("log", text.strip()))
    def flush(self):
        self._stdout.flush()


def _run_agent(location, property_type, max_results):
    global _is_running, _result
    _is_running = True
    _result     = {}

    old_stdout = sys.stdout
    sys.stdout = StreamCapture(_log_queue)
    try:
        result  = orchestrator_agent(location, property_type, max_results)
        _result = result
    except Exception as e:
        _result = {"status": "error", "message": str(e), "leads": []}
    finally:
        sys.stdout  = old_stdout
        _is_running = False
        _log_queue.put(("done", ""))   # sentinel


# ─────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>STR Lead Agent</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:      #0d0d0d;
    --surface: #151515;
    --border:  #222;
    --accent:  #c8f135;
    --muted:   #555;
    --text:    #e8e8e8;
    --subtext: #888;
    --danger:  #ff5f5f;
    --radius:  6px;
    --mono:    'DM Mono', monospace;
    --sans:    'DM Sans', sans-serif;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--text);
    font-family: var(--sans); font-size: 14px;
    min-height: 100vh; padding: 48px 24px;
  }
  .wrap { max-width: 960px; margin: 0 auto; }

  /* Header */
  .header { margin-bottom: 40px; }
  .header h1 {
    font-size: 28px; font-weight: 600; letter-spacing: -0.5px;
    color: var(--accent); font-family: var(--mono);
  }
  .header p { color: var(--subtext); margin-top: 6px; font-size: 13px; }

  /* Card */
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px; margin-bottom: 24px;
  }
  .form-grid {
    display: grid; grid-template-columns: 1fr 1fr auto;
    gap: 12px; align-items: end;
  }
  .field label {
    display: block; font-size: 11px; font-weight: 500;
    letter-spacing: .08em; text-transform: uppercase;
    color: var(--subtext); margin-bottom: 6px; font-family: var(--mono);
  }
  input[type="text"], input[type="number"] {
    width: 100%; background: var(--bg); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text);
    font-family: var(--sans); font-size: 13px;
    padding: 10px 12px; outline: none; transition: border-color .15s;
  }
  input:focus { border-color: var(--accent); }
  .btn {
    background: var(--accent); color: #000; border: none;
    border-radius: var(--radius); font-family: var(--mono);
    font-size: 13px; font-weight: 500; padding: 10px 20px;
    cursor: pointer; white-space: nowrap; height: 40px; transition: opacity .15s;
  }
  .btn:hover { opacity: .85; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }

  /* Activity log */
  .log-wrap {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); margin-bottom: 24px; overflow: hidden;
    display: none;
  }
  .log-wrap.visible { display: block; }
  .log-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 16px; border-bottom: 1px solid var(--border);
  }
  .log-title {
    font-family: var(--mono); font-size: 11px; color: var(--subtext);
    text-transform: uppercase; letter-spacing: .08em;
  }
  .log-status {
    font-family: var(--mono); font-size: 11px; color: var(--accent);
    display: flex; align-items: center; gap: 6px;
  }
  .pulse {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent); animation: pulse 1s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; } 50% { opacity: .3; }
  }
  .log-body {
    font-family: var(--mono); font-size: 11px; color: #666;
    padding: 12px 16px; max-height: 240px; overflow-y: auto;
    line-height: 1.8;
  }
  .log-line { display: block; }
  .log-line .ts { color: var(--muted); margin-right: 8px; }
  .log-line.highlight { color: var(--accent); }
  .log-line.warn { color: #f0a500; }
  .log-line.done { color: var(--accent); font-weight: 500; }

  /* Summary */
  .summary-box {
    display: none; background: rgba(200,241,53,.05);
    border: 1px solid rgba(200,241,53,.2); border-radius: var(--radius);
    padding: 14px 18px; font-size: 13px; color: var(--text);
    margin-bottom: 20px; line-height: 1.6;
  }
  .summary-box.visible { display: block; }
  .summary-label {
    font-family: var(--mono); font-size: 10px; color: var(--accent);
    text-transform: uppercase; letter-spacing: .1em; margin-bottom: 6px;
  }

  /* Stats */
  .stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 24px; }
  .stat {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px;
  }
  .stat-value { font-family: var(--mono); font-size: 28px; font-weight: 500; color: var(--accent); }
  .stat-label { font-size: 11px; color: var(--subtext); text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }

  /* Table */
  .table-wrap {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); overflow: hidden;
  }
  .table-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 14px 18px; border-bottom: 1px solid var(--border);
  }
  .table-title { font-family: var(--mono); font-size: 12px; color: var(--subtext); text-transform: uppercase; letter-spacing: .08em; }
  .refresh-btn {
    background: none; border: 1px solid var(--border); border-radius: var(--radius);
    color: var(--subtext); font-family: var(--mono); font-size: 11px;
    padding: 4px 10px; cursor: pointer; transition: border-color .15s, color .15s;
  }
  .refresh-btn:hover { border-color: var(--accent); color: var(--accent); }
  table { width: 100%; border-collapse: collapse; }
  thead th {
    padding: 10px 14px; text-align: left; font-family: var(--mono);
    font-size: 10px; font-weight: 500; letter-spacing: .1em;
    text-transform: uppercase; color: var(--muted);
    border-bottom: 1px solid var(--border); background: var(--bg);
  }
  tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: rgba(200,241,53,.03); }
  tbody td {
    padding: 11px 14px; font-size: 13px; vertical-align: top;
    max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .tag {
    display: inline-block; font-family: var(--mono); font-size: 10px;
    padding: 2px 7px; border-radius: 3px;
    background: rgba(200,241,53,.1); color: var(--accent);
  }
  .tag.none { background: rgba(255,255,255,.04); color: var(--muted); }
  a { color: var(--accent); text-decoration: none; font-family: var(--mono); font-size: 11px; }
  a:hover { text-decoration: underline; }
  .empty { padding: 48px; text-align: center; color: var(--muted); font-family: var(--mono); font-size: 12px; }
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <h1>STR_LEAD_AGENT</h1>
    <p>Find short-term rental property management companies by location.</p>
  </div>

  <!-- Form -->
  <div class="card">
    <div class="form-grid">
      <div class="field">
        <label>Location</label>
        <input type="text" id="location" placeholder="e.g. Gold Coast, Australia"/>
      </div>
      <div class="field">
        <label>Property Type</label>
        <input type="text" id="property_type" placeholder="e.g. vacation rental"/>
      </div>
      <div class="field">
        <label>Max</label>
        <input type="number" id="max_results" value="5" min="1" max="10" style="width:70px"/>
      </div>
    </div>
    <button class="btn" id="search-btn" onclick="startSearch()" style="margin-top:16px">
      Run Agent
    </button>
  </div>

  <!-- Activity Log -->
  <div class="log-wrap" id="log-wrap">
    <div class="log-header">
      <span class="log-title">Activity Log</span>
      <span class="log-status" id="log-status">
        <span class="pulse" id="log-pulse"></span>
        <span id="log-status-text">Running...</span>
      </span>
    </div>
    <div class="log-body" id="log-body"></div>
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

  <!-- Table -->
  <div class="table-wrap">
    <div class="table-header">
      <span class="table-title">Leads</span>
      <button class="refresh-btn" onclick="loadLeads()">↻ Refresh</button>
    </div>
    <table>
      <thead>
        <tr>
          <th>Company</th><th>Website</th><th>Email</th>
          <th>Phone</th><th>Social</th><th>Location</th>
        </tr>
      </thead>
      <tbody id="results-body">
        <tr><td colspan="6" class="empty">No leads yet — run the agent above.</td></tr>
      </tbody>
    </table>
  </div>

</div>
<script>
  let es = null;

  function appendLog(msg) {
    const body = document.getElementById('log-body');
    const line = document.createElement('span');
    line.className = 'log-line';

    const now = new Date().toTimeString().slice(0,8);
    let cls = '';
    if (msg.includes('Done') || msg.includes('Saved') || msg.includes('Found')) cls = 'highlight';
    if (msg.includes('Warning') || msg.includes('Skipping'))  cls = 'warn';
    if (msg.includes('==='))  return;   // skip divider lines

    line.className = 'log-line ' + cls;
    line.innerHTML = `<span class="ts">${now}</span>${msg}`;
    body.appendChild(line);
    body.scrollTop = body.scrollHeight;
  }

  async function startSearch() {
    const location      = document.getElementById('location').value.trim();
    const property_type = document.getElementById('property_type').value.trim();
    const max_results   = parseInt(document.getElementById('max_results').value) || 5;

    if (!location)      { alert('Please enter a location'); return; }
    if (!property_type) { alert('Please enter a property type'); return; }

    // Reset UI
    const btn = document.getElementById('search-btn');
    btn.disabled  = true;
    btn.innerText = 'Running...';
    document.getElementById('log-body').innerHTML = '';
    document.getElementById('log-wrap').className = 'log-wrap visible';
    document.getElementById('log-pulse').style.display = 'block';
    document.getElementById('log-status-text').innerText = 'Running...';
    document.getElementById('summary-box').className = 'summary-box';

    // Open SSE stream FIRST
    if (es) es.close();
    es = new EventSource('/api/stream');

    es.addEventListener('log', e => {
      appendLog(e.data);
    });

    es.addEventListener('done', e => {
      es.close();
      document.getElementById('log-pulse').style.display = 'none';
      document.getElementById('log-status-text').innerText = 'Complete';
      btn.disabled  = false;
      btn.innerText = 'Run Agent';

      // Fetch final result
      fetch('/api/result').then(r => r.json()).then(data => {
        if (data.summary) {
          document.getElementById('summary-text').innerText = data.summary;
          document.getElementById('summary-box').className = 'summary-box visible';
        }
        appendLog('Done — ' + (data.leads_found || 0) + ' leads saved.');
        loadLeads();
      });
    });

    es.onerror = () => {
      document.getElementById('log-status-text').innerText = 'Error';
      btn.disabled  = false;
      btn.innerText = 'Run Agent';
    };

    // Start search
    await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location, property_type, max_results })
    });
  }

  async function loadLeads() {
    const res   = await fetch('/api/leads');
    const leads = await res.json();
    const tbody = document.getElementById('results-body');

    if (!leads.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty">No leads yet — run the agent above.</td></tr>';
      document.getElementById('stats').style.display = 'none';
      return;
    }

    const withEmail  = leads.filter(l => l.email).length;
    const withSocial = leads.filter(l => l.social_media).length;
    document.getElementById('stat-total').innerText  = leads.length;
    document.getElementById('stat-email').innerText  = withEmail;
    document.getElementById('stat-social').innerText = withSocial;
    document.getElementById('stats').style.display   = 'grid';

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
    global _log_queue, _result, _is_running

    if _is_running:
        return jsonify({"error": "Agent already running"}), 429

    data          = request.get_json()
    location      = data.get("location", "").strip()
    property_type = data.get("property_type", "short-term rental").strip()
    max_results   = min(int(data.get("max_results", 5)), 10)

    if not location:
        return jsonify({"error": "location is required"}), 400

    # Clear queue
    while not _log_queue.empty():
        try: _log_queue.get_nowait()
        except: break

    # Run agent in background thread
    t = threading.Thread(
        target=_run_agent,
        args=(location, property_type, max_results),
        daemon=True
    )
    t.start()

    return jsonify({"status": "started"})


@app.route("/api/stream")
def stream():
    """SSE endpoint — streams log lines until agent is done."""
    def generate():
        yield "retry: 1000\n\n"
        while True:
            try:
                event, data = _log_queue.get(timeout=30)
                if event == "done":
                    yield "event: done\ndata: done\n\n"
                    break
                else:
                    # Escape newlines for SSE
                    safe = data.replace("\n", " ")
                    yield f"event: log\ndata: {safe}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/api/result")
def result():
    return jsonify(_result)


@app.route("/api/leads")
def leads():
    return jsonify(get_all_leads())


@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    init_db()
    print("STR Lead Agent running at http://localhost:5002")
    # threaded=True required for SSE + concurrent requests
    # use_reloader=False prevents double-thread issues
    app.run(port=5002, debug=True, threaded=True, use_reloader=False)