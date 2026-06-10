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
print("BOT TOKEN:", BOT_TOKEN)