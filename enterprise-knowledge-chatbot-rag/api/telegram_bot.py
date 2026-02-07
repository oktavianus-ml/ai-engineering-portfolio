import os
import json
from pathlib import Path

from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from telegram import error


from api.chat_engine import handle_chat_engine
from dotenv import load_dotenv

# =========================
# ENV
# =========================
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# =========================
# LOAD PRODUCTS (WAJIB)
# =========================
ROOT_DIR = Path(__file__).resolve().parent.parent
PRODUCT_FILE = ROOT_DIR / "data/json/products.json"

with open(PRODUCT_FILE, encoding="utf-8") as f:
    PRODUCTS = json.load(f)


# =========================
# TELEGRAM HANDLER
# =========================
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    answer, _ = handle_chat_engine(
        message=text,
        user_id=str(user_id),
        platform="telegram",
        products_data=PRODUCTS
    )

    # Telegram limit ~4096 char
    if len(answer) > 4000:
        answer = answer[:4000]
    try:
        await update.message.reply_text(answer)
    except NetworkError as e:
        print("⚠️ TELEGRAM NETWORK ERROR:", e)

# =========================
# RUN BOT
# =========================
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    print("🤖 Telegram Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
