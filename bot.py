import os
import pandas as pd
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

RAW_CSV_URL = "https://raw.githubusercontent.com/cankale/medicine_bot/main/medicines.csv"

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check <medicine name>")
        return

    df = pd.read_csv(RAW_CSV_URL)
    name = context.args[0].lower()
    found = df['medicine'].str.lower().eq(name).any()

    if found:
        await update.message.reply_text(f"✅ Yes, you have {context.args[0]}")
    else:
        await update.message.reply_text(f"❌ No, you don't have {context.args[0]}")

app = ApplicationBuilder().token(os.environ.get("MEDICINE_BOT_API_KEY")).build()
app.add_handler(CommandHandler("check", check))
app.run_polling()