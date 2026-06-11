import os
import json
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
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

google_creds = json.loads(creds_raw)
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
# COMMANDS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Expense Tracker Ready!\n\n"
        "Example:\n"
        "/expense 120 Food Lunch"
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

        await update.message.reply_text(f"✅ Added ₹{amount} for {category}")

    except Exception as e:
        print("ERROR:", str(e))
        await update.message.reply_text("Usage:\n/expense 120 Food Lunch")

# =====================
# MAIN
# =====================
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("expense", expense))

print("Bot Started Successfully")
app.run_polling()