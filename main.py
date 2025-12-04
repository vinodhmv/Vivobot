from flask import Flask, request, jsonify
import requests
import json
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ------------------------------------------
# CONFIGURATION
# ------------------------------------------
WHATSAPP_TOKEN = "EAAR4KSbGC0IBQNXOf4norJ0Rx0Nraqq12w6qFUCJ7em1dtTCm6lKLzszCFfu7vNH3NE1ZBGM2GsWXXtCHJrahNwBZCPhAX3dabk4Icn5Iobt5pBHR98rFwgXejrEFoqtgJMAxjyv9cfpdQeshByodCLItZBkFdvmPbqHXJsIZBm8CUFs69ROFa1tqwWbqvbCx0t9f2EM14bjM1qyixwPqzgdIDSNDfU3bS57c6KQolFamUyn6wCwdTmuO71w7oZAHnf06qQLSrTfZCcgEzAtlZBd7n23BPUQe1O1ZCQZD"
PHONE_NUMBER_ID = "949447858243959"
VERIFY_TOKEN = "VIVO_REALTY_2025"
GOOGLE_SHEET_NAME = "Vivo_Leads"
SALES_GROUP_ID = "WHATSAPP_GROUP_PLACEHOLDER"  # Add later

# ------------------------------------------
# GOOGLE SHEET SETUP
# ------------------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1

# ------------------------------------------
# FLASK APP
# ------------------------------------------
app = Flask(__name__)

# ------------------------------------------
# VERIFY WEBHOOK (META)
# ------------------------------------------
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403

# ------------------------------------------
# HANDLE INCOMING WHATSAPP MESSAGES
# ------------------------------------------
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()
    try:
        entry = data['entry'][0]['changes'][0]['value']['messages'][0]
        phone = entry["from"]
        user_msg = entry["text"]["body"].strip().lower()

        # Conversation Handling Logic
        reply = process_user_message(phone, user_msg)

        send_whatsapp_message(phone, reply)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error"}), 200

# ------------------------------------------
# MESSAGE PROCESSING LOGIC
# ------------------------------------------
def process_user_message(phone, message):

    # --------------------------------------
    # WELCOME MESSAGE
    # --------------------------------------
    if message in ["hi", "hello", "menu", "start"]:
        return (
            "Hi! 👋 Welcome to *Vivo Realty*.\n"
            "I'm your AI assistant.\n\n"
            "How can I help you today?\n\n"
            "1️⃣ Araise by Hiliving\n"
            "2️⃣ Madhavaram Project\n"
            "3️⃣ Elephantine Garuda\n"
            "4️⃣ Fairmont Estates\n"
            "5️⃣ Book Site Visit\n"
            "6️⃣ Talk to a Human\n"
        )

    # --------------------------------------
    # PROJECT REPLIES
    # --------------------------------------
    if message == "1":
        return (
            "*Araise by Hiliving*\n"
            "📍 Near Tiruvottiyur Metro\n"
            "Premium plotted development 600–1800 sq ft.\n"
            "High appreciation zone.\n\n"
            "Reply: 'site visit' or 'details'"
        )

    if message == "2":
        return (
            "*Madhavaram Project — Perungavur*\n"
            "14 km from Anna Nagar.\n"
            "💰 Current Price: ₹2400/sq ft\n"
            "Metro expansion soon.\n\n"
            "Reply: 'layout', 'pricing', or 'site visit'"
        )

    if message == "3":
        return (
            "*Elephantine Garuda*\n"
            "Villa community near Chengalpattu.\n"
            "600–2400 sq ft plots.\n\n"
            "Reply: 'availability' or 'site visit'"
        )

    if message == "4":
        return (
            "*Fairmont Estates – Parivakkam*\n"
            "Near Poonamallee.\n"
            "Limited premium plots.\n\n"
            "Reply: 'plots' or 'site visit'"
        )

    # --------------------------------------
    # SITE VISIT BOOKING
    # --------------------------------------
    if "site visit" in message:
        return (
            "Super! 👍\n"
            "Please send your *Name*."
        )

    # --------------------------------------
    # NAME CAPTURE
    # --------------------------------------
    if "my name is" in message or len(message.split()) == 1 and message.isalpha():
        name = message.replace("my name is", "").strip().title()
        save_to_sheet(name, phone, "Site Visit Request", "NA")
        notify_sales_group(name, phone)
        return (
            f"Thanks {name} 😊\n"
            "Your site visit request is received.\n"
            "Our team will contact you shortly.\n"
            "Do you want to choose: Today, Tomorrow, Weekend?"
        )

    return (
        "I'm here to help 😊\n"
        "Type *menu* to see all options again."
    )

# ------------------------------------------
# SAVE TO GOOGLE SHEET
# ------------------------------------------
def save_to_sheet(name, phone, project, budget):
    sheet.append_row([
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        name,
        phone,
        project,
        budget
    ])

# ------------------------------------------
# SEND MESSAGE TO WHATSAPP GROUP
# ------------------------------------------
def notify_sales_group(name, phone):
    msg = (
        f"🔥 *New Lead Alert*\n"
        f"Name: {name}\n"
        f"Phone: {phone}\n"
        f"Source: WhatsApp Bot\n"
    )
    send_whatsapp_message(SALES_GROUP_ID, msg)

# ------------------------------------------
# SEND MESSAGE FUNCTION
# ------------------------------------------
def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }

    requests.post(url, headers=headers, data=json.dumps(payload))


# ------------------------------------------
if __name__ == '__main__':
    app.run(port=5000)
