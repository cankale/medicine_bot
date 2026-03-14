import os
import pandas as pd
import requests
import base64
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import Update

RAW_CSV_URL = "https://raw.githubusercontent.com/cankale/medicine_bot/main/medicines.csv"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com/repos/cankale/medicine_bot/contents/medicines.csv"

CONFIRM_DELETE = 1
pending_delete = {}

def get_csv():
    df = pd.read_csv(RAW_CSV_URL)
    return df

def push_csv(df):
    # Get current file SHA (required by GitHub API)
    response = requests.get(GITHUB_API_URL, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = response.json()["sha"]
    
    # Encode CSV content
    content = df.to_csv(index=False)
    encoded = base64.b64encode(content.encode()).decode()
    
    # Push update
    requests.put(GITHUB_API_URL, 
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json={
            "message": "delete medicine via bot",
            "content": encoded,
            "sha": sha
        }
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check <medicine name>")
        return

    df = get_csv()
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

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delete <medicine name>")
        return ConversationHandler.END

    df = get_csv()
    name = context.args[0].lower()
    match = df[df['medicine'].str.lower() == name]

    if match.empty:
        await update.message.reply_text("❌ Not found")
        return ConversationHandler.END

    row = match.iloc[0]
    pending_delete[update.effective_user.id] = context.args[0]
    await update.message.reply_text(
        f"⚠️ Are you sure you want to delete one unit of {row['medicine']} (adet: {int(row['adet'])})?\n\nReply y or n"
    )
    return CONFIRM_DELETE

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answer = update.message.text.strip().lower()

    if answer != 'y':
        await update.message.reply_text("❌ Cancelled")
        pending_delete.pop(user_id, None)
        return ConversationHandler.END

    medicine_name = pending_delete.pop(user_id, None)
    if not medicine_name:
        await update.message.reply_text("❌ No pending delete")
        return ConversationHandler.END

    df = get_csv()
    name = medicine_name.lower()
    idx = df[df['medicine'].str.lower() == name].index

    if len(idx) == 0:
        await update.message.reply_text("❌ Not found")
        return ConversationHandler.END

    if df.loc[idx[0], 'adet'] <= 1:
        df = df.drop(idx[0]).reset_index(drop=True)
        await update.message.reply_text(f"🗑️ {medicine_name} removed completely")
    else:
        df.loc[idx[0], 'adet'] -= 1
        await update.message.reply_text(f"✅ {medicine_name} adet decreased to {int(df.loc[idx[0], 'adet'])}")

    push_csv(df)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled")
    return ConversationHandler.END

delete_handler = ConversationHandler(
    entry_points=[CommandHandler("delete", delete)],
    states={CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)]},
    fallbacks=[CommandHandler("cancel", cancel)]
)

app = ApplicationBuilder().token(os.environ.get("MEDICINE_BOT_API_KEY")).build()
app.add_handler(CommandHandler("check", check))
app.add_handler(delete_handler)
app.run_polling()