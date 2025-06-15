from flask import Flask, request, jsonify
import json, os, gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from difflib import SequenceMatcher

app = Flask(__name__)

SPREADSHEET_ID = "1sGdsa3oShUwGrxADKlJT3-QVmKVji8mYuUwQjtxsMp4"

def get_sheet():
    creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok"}), 200

@app.route("/case", methods=["POST"])
def save_case():
    data = request.get_json()
    user = data.get("user")
    document_type = data.get("document_type", "")
    question = data.get("question")
    solution = data.get("solution")
    tags = data.get("tags", "")
    if not (user and question and solution):
        return jsonify({"error": "Missing fields"}), 400
    sheet = get_sheet()
    sheet.append_row([datetime.now().isoformat(), user, document_type, question, solution, tags])
    return jsonify({"status": "saved"}), 200

@app.route("/case", methods=["GET"])
def find_case():
    question = request.args.get("question", "").strip().lower()
    if not question:
        return jsonify({"error": "Missing question"}), 400

    sheet = get_sheet()
    all_rows = sheet.get_all_records()
    matches = []

    for row in all_rows:
        q = row.get("question", "")
        if not q:
            continue
        ratio = SequenceMatcher(None, question, q.lower()).ratio()
        if ratio >= 0.6:
            row["match_ratio"] = round(ratio, 2)
            matches.append(row)

    matches.sort(key=lambda x: x["match_ratio"], reverse=True)
    return jsonify({"matches": matches})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
