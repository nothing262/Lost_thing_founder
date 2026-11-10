"""Campus Lost and Found Matcher - RGUKT DAA Project 5.
Standalone local browser app. Uses only Python standard library.
"""
import json
import re
import html
import os
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

DATA_FILE = Path(__file__).with_name("data.json")
PORT = int(os.environ.get("PORT", "8000"))
STATUSES = ["Reported", "Matched", "Returned"]
KINDS = ["Lost", "Found"]

def load_data():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("reports"), list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"reports": []}

def save_data(data):
    temp = DATA_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(DATA_FILE)

def esc(value):
    return html.escape(str(value), quote=True)

def matches(report, reports):
    """Return opposite-kind, same-category candidates ranked by transparent score."""
    results = []
    words = set(re.findall(r"\w+", report["description"].lower()))
    for other in reports:
        if other["id"] == report["id"]:
            continue
        if other["kind"] == report["kind"] or other["status"] == "Returned":
            continue
        if other["category"].lower() != report["category"].lower():
            continue
        shared = words & set(re.findall(r"\w+", other["description"].lower()))
        score, reasons = 3, ["Same category (+3)"]
        if shared:
            score += len(shared)
            reasons.append("Shared words: " + ", ".join(sorted(shared)) + f" (+{len(shared)})")
        if other["location"].lower() == report["location"].lower():
            score += 2
            reasons.append("Same location (+2)")
        gap = abs((date.fromisoformat(report["date"]) -
                   date.fromisoformat(other["date"])).days)
        if gap <= 3:
            score += 1
            reasons.append("Dates within 3 days (+1)")
        results.append({"id": other["id"], "score": score,
                        "reasons": "; ".join(reasons),
                        "description": other["description"],
                        "kind": other["kind"], "location": other["location"],
                        "date": other["date"], "status": other["status"]})
    return sorted(results, key=lambda row: (-row["score"], row["id"]))

def render_table(headers, rows):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>"
    if not body:
        body = f'<tr><td colspan="{len(headers)}">No records</td></tr>'
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

def form(action, fields, button):
    out = f'<form method="post"><input type="hidden" name="action" value="{esc(action)}">'
    for name, label, kind, value in fields:
        out += f'<label>{esc(label)}'
        if kind == "select":
            out += f'<select name="{esc(name)}" required>'
            for option in value:
                out += f'<option value="{esc(option)}">{esc(option)}</option>'
            out += "</select>"
        else:
            out += f'<input type="{esc(kind)}" name="{esc(name)}" value="{esc(value)}" required>'
        out += "</label>"
    return out + f'<button type="submit">{esc(button)}</button></form>'

def page(message=""):
    data = load_data()
    today = date.today().isoformat()
    content = """
    <p class="hint">Use fictional item reports only. Match scores are suggestions, not proof of ownership.
    No contact details are collected.</p>
    """
    content += form("add", [
        ("kind", "Report type", "select", KINDS),
        ("category", "Category", "text", "Bottle"),
        ("description", "Description", "text", "Blue steel bottle"),
        ("location", "Location", "text", "Library"),
        ("date", "Date", "date", today)], "Add report")
    content += form("search", [("query", "Category or description keyword", "text", "bottle")], "Search reports")
    content += form("match", [("id", "Report ID for match suggestions", "number", "1")], "Suggest matches")
    content += form("status", [
        ("id", "Report ID", "number", "1"),
        ("status", "New status", "select", STATUSES)], "Update status")
    # Extension: linked report pair can be marked Matched/Returned together.
    content += form("link", [
        ("lost_id", "Lost report ID", "number", "1"),
        ("found_id", "Found report ID", "number", "2")], "Link verified Lost + Found pair")
    content += "<h2>All reports</h2>"
    content += render_table(["ID","Kind","Category","Description","Location","Date","Status"],
        [[r["id"],r["kind"],r["category"],r["description"],r["location"],r["date"],r["status"]]
         for r in data["reports"]])
    content += '<p class="hint">Extension: linking a verified pair updates both reports together to Matched. Marking either linked report Returned also marks its partner Returned.</p>'
    banner = f'<div class="message">{esc(message)}</div>' if message else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Campus Lost and Found Matcher</title><style>
    *{{box-sizing:border-box}} body{{font:16px system-ui;background:#eef2f6;color:#182638;margin:0}}
    main{{max-width:1050px;margin:24px auto;padding:22px;background:white;border-radius:12px}}
    h1{{font-size:28px}}h2{{margin-top:28px;font-size:21px}}
    form{{padding:14px;border:1px solid #cbd5e1;border-radius:8px;margin:12px 0}}
    label{{display:block;margin:10px 0}}input,select{{display:block;width:100%;padding:9px;font:inherit;border:1px solid #94a3b8;border-radius:5px;margin-top:5px}}
    button{{background:#164e83;color:white;border:0;padding:10px 18px;border-radius:5px;font:inherit;cursor:pointer}}
    table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #cbd5e1;padding:9px;text-align:left;white-space:pre-wrap}}th{{background:#e2e8f0}}
    .scroll{{overflow:auto}}.hint{{color:#475569}}.message{{padding:12px;background:#e0f2fe;border-radius:7px;margin:12px 0}}
    </style></head><body><main><h1>Campus Lost and Found Matcher</h1>
    <p>DAA Project 5 | Local learning application</p>{banner}{content}</main></body></html>"""

def handle(data):
    records = load_data()["reports"]
    action = data.get("action", "")
    if action == "add":
        try:
            date.fromisoformat(data.get("date", ""))
        except ValueError:
            raise ValueError("Enter a valid date in YYYY-MM-DD format.")
        if data.get("kind") not in KINDS:
            raise ValueError("Choose Lost or Found.")
        for key in ("category", "description", "location"):
            if not data.get(key, "").strip():
                raise ValueError("Category, description and location cannot be blank.")
        record = {
            "id": max((r["id"] for r in records), default=0) + 1,
            "kind": data["kind"], "category": data["category"].strip(),
            "description": data["description"].strip(),
            "location": data["location"].strip(), "date": data["date"],
            "status": "Reported", "linked_id": None
        }
        records.append(record)
        save_data({"reports": records})
        return f"Report #{record['id']} added successfully."
    if action == "search":
        query = data.get("query", "").strip().lower()
        found = [r for r in records if query in (r["category"] + " " + r["description"]).lower()]
        return "Search results for " + (query or "(all)") + ": " + str(len(found)) + " report(s).\\n" + json.dumps(found, indent=2)
    if action in ("match", "status"):
        try:
            rid = int(data.get("id", ""))
        except ValueError:
            raise ValueError("Report ID must be a number.")
        report = next((r for r in records if r["id"] == rid), None)
        if report is None:
            raise ValueError("Report ID does not exist.")
        if action == "match":
            if report["status"] == "Returned":
                raise ValueError("This report is already closed.")
            candidates = matches(report, records)
            return "Possible matches for report #" + str(rid) + ":\\n" + json.dumps(candidates, indent=2)
        status = data.get("status")
        if status not in STATUSES:
            raise ValueError("Invalid status.")
        report["status"] = status
        linked_id = report.get("linked_id")
        if linked_id is not None and status == "Returned":
            partner = next((r for r in records if r["id"] == linked_id), None)
            if partner:
                partner["status"] = "Returned"
        save_data({"reports": records})
        return f"Report #{rid} status updated to {status}."
    if action == "link":
        try:
            lost_id, found_id = int(data.get("lost_id", "")), int(data.get("found_id", ""))
        except ValueError:
            raise ValueError("Both report IDs must be numbers.")
        lost = next((r for r in records if r["id"] == lost_id), None)
        found = next((r for r in records if r["id"] == found_id), None)
        if not lost or not found:
            raise ValueError("One or both report IDs do not exist.")
        if lost["kind"] != "Lost" or found["kind"] != "Found":
            raise ValueError("Choose a Lost report first and a Found report second.")
        if lost["id"] == found["id"]:
            raise ValueError("A report cannot be linked to itself.")
        if lost["category"].lower() != found["category"].lower():
            raise ValueError("The reports must have the same category.")
        lost["linked_id"], found["linked_id"] = found["id"], lost["id"]
        lost["status"] = found["status"] = "Matched"
        save_data({"reports": records})
        return f"Reports #{lost_id} and #{found_id} linked and marked Matched."
    raise ValueError("Unknown action.")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        self.send_page(page())
    def do_POST(self):
        try:
            if self.path != "/":
                raise ValueError("Unknown page.")
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 1_000_000:
                raise ValueError("Request is empty or too large.")
            raw = self.rfile.read(length).decode("utf-8")
            data = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
            message = handle(data)
            self.send_page(page(message))
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
            self.send_page(page("Please check: " + str(error)))
    def send_page(self, html_text):
        body = html_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Campus Lost and Found Matcher: open http://127.0.0.1:{PORT}")
    print("Keep this terminal open. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
