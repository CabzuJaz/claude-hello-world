from flask import Flask, jsonify, request, render_template_string
from database import init_db, get_all_leads, save_lead
from sheets import append_lead
from datetime import datetime

app = Flask(__name__)

# Initialize DB on startup
init_db()

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>STR Lead Agent</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { font-size: 24px; }
        input, select { padding: 8px; margin: 4px 0; width: 100%; box-sizing: border-box; }
        button { padding: 10px 20px; background: #000; color: #fff; border: none; cursor: pointer; margin-top: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
        th { background: #f5f5f5; }
        #status { margin-top: 12px; font-size: 13px; color: #666; }
    </style>
</head>
<body>
    <h1>STR Lead Research Agent</h1>
    <p>Find short-term rental property managers by location.</p>

    <label>Location</label>
    <input type="text" id="location" placeholder="e.g. Sydney, Australia" />

    <label>Property Type</label>
    <input type="text" id="property_type" placeholder="e.g. vacation rental, serviced apartment" />

    <label>Max Results</label>
    <input type="number" id="max_results" value="10" min="1" max="50" />

    <button onclick="startSearch()">Find Leads</button>
    <div id="status"></div>

    <table id="results" style="display:none">
        <thead>
            <tr>
                <th>Company</th>
                <th>Website</th>
                <th>Email</th>
                <th>Location</th>
                <th>Found Via</th>
            </tr>
        </thead>
        <tbody id="results-body"></tbody>
    </table>

    <script>
        async function startSearch() {
            const location = document.getElementById('location').value;
            const property_type = document.getElementById('property_type').value;
            const max_results = document.getElementById('max_results').value;

            if (!location) { alert('Please enter a location'); return; }

            document.getElementById('status').innerText = 'Agent is searching...';

            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location, property_type, max_results })
            });

            const data = await response.json();
            document.getElementById('status').innerText = data.message;
            loadLeads();
        }

        async function loadLeads() {
            const response = await fetch('/api/leads');
            const leads = await response.json();

            const tbody = document.getElementById('results-body');
            tbody.innerHTML = '';

            leads.forEach(lead => {
                tbody.innerHTML += `<tr>
                    <td>${lead.company_name}</td>
                    <td>${lead.website ? '<a href="' + lead.website + '" target="_blank">Visit</a>' : '-'}</td>
                    <td>${lead.email || '-'}</td>
                    <td>${lead.location}</td>
                    <td>${lead.source}</td>
                </tr>`;
            });

            document.getElementById('results').style.display = 'table';
        }

        // Load existing leads on page load
        loadLeads();
    </script>
</body>
</html>
""")

@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json()
    location = data.get("location")
    property_type = data.get("property_type", "short-term rental")
    max_results = int(data.get("max_results", 10))

    if not location:
        return jsonify({"error": "location is required"}), 400

    # Placeholder — Claude agent goes here on Day 24
    print(f"[API] Search request: {location} | {property_type} | max: {max_results}")

    # Test save for now
    save_lead(
        company_name="Test STR Management Co",
        website="https://example.com",
        email="contact@example.com",
        phone="+1 555 0000",
        linkedin_url="https://linkedin.com/company/example",
        location=location,
        source="test"
    )
    append_lead(
        company_name="Test STR Management Co",
        website="https://example.com",
        email="contact@example.com",
        location=location,
        source="test"
    )

    return jsonify({
        "status": "ok",
        "message": f"Search started for {location}. Agent will populate results shortly."
    })

@app.route("/api/leads", methods=["GET"])
def leads():
    return jsonify(get_all_leads())

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    print("STR Lead Agent running at http://localhost:5002")
    app.run(port=5002, debug=True)