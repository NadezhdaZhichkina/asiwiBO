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
    question = request.args.get("question", "").lower()
    document_type = request.args.get("document_type", "").lower()
    if not question:
        return jsonify({"error": "Missing question"}), 400
    sheet = get_sheet()
    all_rows = sheet.get_all_records()
    best_match = None
    best_ratio = 0
    for row in all_rows:
        if document_type and row.get("document_type", "").lower() != document_type:
            continue
        q = row.get("question", "").lower()
        if not q:
            continue
        ratio = SequenceMatcher(None, question, q).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = row
    return jsonify({
        "match_ratio": round(best_ratio, 2),
        "matched_case": best_match
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
