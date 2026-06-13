import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import gspread
from google import genai
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime

print("=== BOT STARTING ===")

# =====================
# LOAD CREDENTIALS
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found")

creds_raw = os.getenv("GOOGLE_CREDENTIALS")
if not creds_raw:
    raise ValueError("GOOGLE_CREDENTIALS not found")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

google_creds = json.loads(creds_raw)
google_creds["private_key"] = google_creds["private_key"].replace("\\n", "\n")
print("Credentials loaded successfully")

# =====================
# CONNECT GOOGLE SHEETS
# =====================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(google_creds, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1szlGWdA8GWq9jkzAm3ZGxFbbuaGNbXeiIFjQoA26fyM").worksheet("Sheet1")
print("Google Sheets connected successfully")

# =====================
# SETUP GEMINI
# =====================
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
print("Gemini AI connected successfully")

# =====================
# KEEP-ALIVE SERVER
# =====================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, format, *args):
        pass

def run_server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# =====================
# GEMINI PARSER
# =====================
def parse_expense_with_gemini(text):
    prompt = f"""
Extract expense details from this message: "{text}"

Rules:
- amount: the number (integer or decimal), no currency symbol
- category: one of these only — Food, Transport, Shopping, Entertainment, Health, Bills, Education, Other
- description: short 1-3 word description of what was spent on

Respond ONLY with a JSON object like this:
{{"amount": 120, "category": "Food", "description": "Lunch"}}

If you cannot find an amount, respond with:
{{"error": "no amount found"}}
"""
    try:
        
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text_response = response.text.strip()
        # Clean markdown if present
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        data = json.loads(text_response)
        return data
    except Exception as e:
        print("Gemini error:", str(e))
        return {"error": str(e)}

# =====================
# COMMANDS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Expense Tracker Ready!\n\n"
        "You can add expenses in two ways:\n\n"
        "1️⃣ Command format:\n"
        "/expense 120 Food Lunch\n\n"
        "2️⃣ Natural language:\n"
        "spent 120 on lunch\n"
        "200 at dominos\n"
        "auto 50\n"
        "chai 20"
    )

async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            await update.message.reply_text("Usage:\n/expense 120 Food Lunch")
            return
        amount = context.args[0]
        category = context.args[1]
        description = " ".join(context.args[2:])
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            amount,
            category,
            description
        ])
        await update.message.reply_text(
            f"✅ Added ₹{amount} for {category}\n"
            f"📝 {description}"
        )
    except Exception as e:
        print("ERROR:", str(e))
        await update.message.reply_text("Usage:\n/expense 120 Food Lunch")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text("🤔 Processing...")

    result = parse_expense_with_gemini(text)

    if "error" in result:
        await update.message.reply_text(
            "❌ Could not detect amount.\n\n"
            "Try:\n"
            "• spent 150 on groceries\n"
            "• 200 at dominos\n"
            "• auto 50"
        )
        return

    amount = result.get("amount")
    category = result.get("category", "Other")
    description = result.get("description", text)

    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        amount,
        category,
        description
    ])

    await update.message.reply_text(
        f"✅ Added ₹{amount} for {category}\n"
        f"📝 {description}\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

# =====================
# MAIN
# =====================
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("expense", expense))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot Started Successfully")
app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
