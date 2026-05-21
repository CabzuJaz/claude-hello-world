from flask import Flask, jsonify, request, render_template_string, Response, stream_with_context
from database import init_db, get_all_leads
from agent import orchestrator_agent
from config import FLASK_PORT, FLASK_DEBUG, MAX_RESULTS_LIMIT, validate_config
from datetime import datetime
import queue
import threading
import sys
import html as html_lib

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB request limit

# ─────────────────────────────────────────
# GLOBAL STATE — single-user sprint tool
# ─────────────────────────────────────────

_log_queue  = queue.Queue()
_result     = {}
_is_running = False


class StreamCapture:
    """Captures print() output → log queue + terminal."""
    def __init__(self, q):
        self.q       = q
        self._stdout = sys.__stdout__
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
        print(f"[Agent] Fatal error: {e}")
    finally:
        sys.stdout  = old_stdout
        _is_running = False          # ✅ always reset — even on crash
        _log_queue.put(("done", ""))


def _sanitize(value: str, max_len: int = 200) -> str:
    """Strip, truncate, and escape HTML entities to prevent XSS."""
    if not value:
        return ""
    return html_lib.escape(str(value).strip()[:max_len])


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
  .header { margin-bottom: 40px; }
  .header h1 {
    font-size: 28px; font-weight: 600; letter-spacing: -0.5px;
    color: var(--accent); font-family: var(--mono);
  }
  .header p { color: var(--subtext); margin-top: 6px; font-size: 13px; }
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
  .log-wrap {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); margin-bottom: 24px; overflow: hidden; display: none;
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
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }
  .log-body {
    font-family: var(--mono); font-size: 11px; color: #666;
    padding: 12px 16px; max-height: 240px; overflow-y: auto; line-height: 1.8;
  }
  .log-line { display: block; }
  .log-line .ts { color: var(--muted); margin-right: 8px; }
  .log-line.highlight { color: var(--accent); }
  .log-line.warn { color: #f0a500; }
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
  .stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 24px; }
  .stat {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px;
  }
  .stat-value { font-family: var(--mono); font-size: 28px; font-weight: 500; color: var(--accent); }
  .stat-label { font-size: 11px; color: var(--subtext); text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }
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
  .err-msg {
    color: var(--danger); font-family: var(--mono); font-size: 12px;
    padding: 10px 14px; border: 1px solid var(--danger);
    border-radius: var(--radius); margin-bottom: 16px; display: none;
  }
  .err-msg.visible { display: block; }
</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <h1>STR_LEAD_AGENT</h1>
    <p>Find short-term rental property management companies by location.</p>
  </div>

  <!-- Error message -->
  <div class="err-msg" id="err-msg"></div>

  <!-- Form -->
  <div class="card">
    <div class="form-grid">
      <div class="field">
        <label>Location</label>
        <input type="text" id="location" placeholder="e.g. Gold Coast, Australia" maxlength="100"/>
      </div>
      <div class="field">
        <label>Property Type</label>
        <input type="text" id="property_type" placeholder="e.g. vacation rental" maxlength="100"/>
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

  function showError(msg) {
    const el = document.getElementById('err-msg');
    el.innerText = msg;
    el.className = 'err-msg visible';
    setTimeout(() => el.className = 'err-msg', 5000);
  }

  function appendLog(msg) {
    const body = document.getElementById('log-body');
    const line = document.createElement('span');
    const now  = new Date().toTimeString().slice(0,8);
    let cls = '';
    if (msg.includes('Done') || msg.includes('Saved') || msg.includes('Found')) cls = 'highlight';
    if (msg.includes('Warning') || msg.includes('Skipping')) cls = 'warn';
    if (msg.includes('===')) return;
    line.className = 'log-line ' + cls;
    line.innerHTML = `<span class="ts">${now}</span>${msg}`;
    body.appendChild(line);
    body.scrollTop = body.scrollHeight;
  }

  async function startSearch() {
    const location      = document.getElementById('location').value.trim();
    const property_type = document.getElementById('property_type').value.trim();
    const max_results   = parseInt(document.getElementById('max_results').value) || 5;

    if (!location)      { showError('Please enter a location'); return; }
    if (!property_type) { showError('Please enter a property type'); return; }
    if (max_results < 1 || max_results > 10) { showError('Max results must be between 1 and 10'); return; }

    const btn = document.getElementById('search-btn');
    btn.disabled  = true;
    btn.innerText = 'Running...';

    document.getElementById('log-body').innerHTML = '';
    document.getElementById('log-wrap').className = 'log-wrap visible';
    document.getElementById('log-pulse').style.display = 'block';
    document.getElementById('log-status-text').innerText = 'Running...';
    document.getElementById('summary-box').className = 'summary-box';
    document.getElementById('err-msg').className = 'err-msg';

    if (es) es.close();
    es = new EventSource('/api/stream');

    es.addEventListener('log', e => appendLog(e.data));

    es.addEventListener('done', e => {
      es.close();
      document.getElementById('log-pulse').style.display = 'none';
      document.getElementById('log-status-text').innerText = 'Complete';
      btn.disabled  = false;
      btn.innerText = 'Run Agent';

      fetch('/api/result').then(r => r.json()).then(data => {
        if (data.status === 'error') {
          showError(data.message || 'Agent error — check terminal');
          return;
        }
        if (data.summary) {
          document.getElementById('summary-text').innerText = data.summary;
          document.getElementById('summary-box').className = 'summary-box visible';
        }
        appendLog('Done — ' + (data.leads_found || 0) + ' leads saved.');
        loadLeads();
      });
    });

    es.onerror = () => {
      document.getElementById('log-status-text').innerText = 'Connection lost';
      btn.disabled  = false;
      btn.innerText = 'Run Agent';
    };

    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location, property_type, max_results })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showError(err.error || 'Search failed — check terminal');
      btn.disabled  = false;
      btn.innerText = 'Run Agent';
      if (es) es.close();
    }
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

    // ✅ textContent prevents XSS — never use innerHTML with user data
    tbody.innerHTML = '';
    leads.forEach(l => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td title="${esc(l.company_name)}">${esc(l.company_name)}</td>
        <td>${l.website ? `<a href="${esc(l.website)}" target="_blank" rel="noopener noreferrer">↗ visit</a>` : '<span class="tag none">—</span>'}</td>
        <td>${l.email    ? `<span class="tag">${esc(l.email)}</span>`    : '<span class="tag none">—</span>'}</td>
        <td>${l.phone    ? `<span class="tag">${esc(l.phone)}</span>`    : '<span class="tag none">—</span>'}</td>
        <td>${l.social_media ? `<a href="${esc(l.social_media)}" target="_blank" rel="noopener noreferrer">↗ social</a>` : '<span class="tag none">—</span>'}</td>
        <td title="${esc(l.location)}">${esc(l.location)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ✅ Client-side HTML escape — prevents XSS in table
  function esc(s) {
    if (!s) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
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
        return jsonify({"error": "Agent already running — wait for it to finish"}), 429

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    # ✅ Sanitize all inputs
    location      = _sanitize(data.get("location", ""))
    property_type = _sanitize(data.get("property_type", "short-term rental"))
    max_results   = int(data.get("max_results", 5))

    if not location:
        return jsonify({"error": "location is required"}), 400
    if not property_type:
        return jsonify({"error": "property_type is required"}), 400

    # ✅ Cap max_results
    max_results = max(1, min(max_results, MAX_RESULTS_LIMIT))

    # Clear queue
    while not _log_queue.empty():
        try: _log_queue.get_nowait()
        except: break

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
                    safe = data.replace("\n", " ")
                    yield f"event: log\ndata: {safe}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/api/result")
def result():
    return jsonify(_result)


@app.route("/api/leads")
def leads():
    return jsonify(get_all_leads())


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "agent_running": _is_running,
        "timestamp": datetime.now().isoformat()
    })


# ─────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(413)
def request_too_large(e):
    return jsonify({"error": "Request body too large (max 1MB)"}), 413

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Agent already running"}), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    validate_config()
    init_db()
    print(f"STR Lead Agent running at http://localhost:{FLASK_PORT}")
    app.run(
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        threaded=True,
        use_reloader=False
    )