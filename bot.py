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
    match = df[df['medicine'].str.lower() == name]

    if not match.empty:
        row = match.iloc[0]
        bbd = row['bbd'] if pd.notna(row['bbd']) and row['bbd'] != '' else 'Girilmedi'
        await update.message.reply_text(
            f"💊 {row['medicine']}\n"
            f"📋 {row['tanim']}\n"
            f"🔢 Adet: {int(row['adet'])}\n"
            f"📅 BBD: {bbd}"
        )
    else:
        await update.message.reply_text("❌ Not found")

app = ApplicationBuilder().token(os.environ.get("MEDICINE_BOT_API_KEY")).build()
app.add_handler(CommandHandler("check", check))
app.run_polling()