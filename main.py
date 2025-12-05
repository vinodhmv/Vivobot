import os
import json
from flask import Flask, request, jsonify
from oauth2client.service_account import ServiceAccountCredentials
import gspread

app = Flask(__name__)

# ==============================
#   GOOGLE SHEETS AUTH (Render)
# ==============================

def get_gsheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]

    # Load credentials from Render ENV
    google_creds = os.environ.get("GOOGLE_CREDENTIALS")

    if not google_creds:
        print("❌ GOOGLE_CREDENTIALS ENV variable missing!")
        raise Exception("GOOGLE_CREDENTIALS not set")

    creds_dict = json.loads(google_creds)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client


# ==============================
#       WHATSAPP WEBHOOK
# ==============================

@app.route("/webhook", methods=["GET"])
def verify_token():
    verify_token = os.environ.get("VERIFY_TOKEN", "VIVO_REALTY_2025")

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    else:
        return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook_message():
    data = request.get_json()

    print("📩 Received WhatsApp message:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        text = message["text"]["body"]

        # Save message to Google Sheet
        save_to_sheet(sender, text)

        return jsonify({"status": "Message saved"}), 200

    except Exception as e:
        print("❌ Webhook Error:", str(e))
        return jsonify({"error": str(e)}), 200


# ==============================
#   SAVE WHATSAPP MESSAGE
# ==============================

def save_to_sheet(sender, message):
    try:
        client = get_gsheet_client()
        sheet = client.open("vivobot").sheet1
        sheet.append_row([sender, message])
        print("✅ Saved to Google Sheets")
    except Exception as e:
        print("❌ Error saving to sheet:", e)


# ==============================
#         ROOT CHECK
# ==============================

@app.route("/")
def home():
    return "VivoBot Running Successfully 🚀"


# ==============================
#         LOCAL TESTING
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
