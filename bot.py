import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

# =====================
# CONFIG
# =====================

load_dotenv()

BOT_TOKEN = BOT_TOKEN = os.getenv("BOT_TOKEN")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

creds = Credentials.from_service_account_file(
    "expense-tracker-499004-283d23e44dbd.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1szlGWdA8GWq9jkzAm3ZGxFbbuaGNbXeiIFjQoA26fyM"
).worksheet("Sheet1")

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
            f"✅ Added ₹{amount} for {category}"
        )

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text(
            "Usage:\n/expense 120 Food Lunch"
        )

# =====================
# MAIN
# =====================
print("BOT TOKEN:", BOT_TOKEN)

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("expense", expense))

print("Bot Started Successfully")

app.run_polling()