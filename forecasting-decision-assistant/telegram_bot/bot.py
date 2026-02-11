from telegram.ext import Application, MessageHandler, filters
from telegram_bot.handlers import handle_message
from app.config.settings import settings


async def on_message(update, context):
    """
    Entry point setiap pesan Telegram.
    Menangani 3 tipe response:
    - list   → legacy (text/image terpisah)
    - str    → legacy text
    - dict   → NEW (text + images dari ChatService)
    """

    user_text = update.message.text
    chat_id = update.effective_chat.id

    # =========================
    # CALL HANDLER (CORE LOGIC)
    # =========================
    try:
        responses = handle_message(
            user_text,
            chat_id=chat_id
        )
    except Exception as e:
        print("[BOT] handler error:", e)
        await update.message.reply_text(
            "Terjadi kesalahan saat memproses permintaan."
        )
        return

    # =========================
    # 1️⃣ HANDLE LIST (LEGACY PIPELINE)
    # =========================
    # Format:
    # [
    #   {"type": "text", "value": "..."},
    #   {"type": "image", "value": "path.png", "caption": "..."}
    # ]
    if isinstance(responses, list):
        for msg in responses:
            msg_type = msg.get("type")

            # TEXT MESSAGE
            if msg_type == "text":
                await update.message.reply_text(
                    msg.get("value", ""),
                    parse_mode=None  # ⛔ matikan markdown (aman)
                )

            # IMAGE MESSAGE
            elif msg_type == "image":
                image_path = msg.get("value")
                caption = msg.get("caption", "")

                if not image_path:
                    continue

                try:
                    with open(image_path, "rb") as img:
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=img,
                            caption=caption,
                            parse_mode=None  # ⛔ hindari markdown error
                        )
                except FileNotFoundError:
                    await update.message.reply_text(
                        "⚠️ Gambar tidak ditemukan."
                    )

        return  # ⛔ STOP di legacy list

    # =========================
    # 2️⃣ HANDLE STRING (LEGACY TEXT)
    # =========================
    if isinstance(responses, str):
        await update.message.reply_text(
            responses,
            parse_mode=None  # ⛔ hindari markdown crash
        )
        return

    # =========================
    # 3️⃣ HANDLE DICT (NEW PIPELINE)
    # =========================
    # Format:
    # {
    #   "text": "...",
    #   "images": {
    #       "weekly": "path.png",
    #       "monthly": "path.png",
    #       "sensitivity": "path.png"
    #   }
    # }
    if isinstance(responses, dict):
        # ---- TEXT FIRST ----
        text = responses.get("text")
        if text:
            await update.message.reply_text(
                text,
                parse_mode=None  # ⛔ aman
            )

        # ---- IMAGES ----
        images = responses.get("images", {})

        for name, image_path in images.items():
            if not image_path:
                continue

            # caption khusus sensitivity
            caption = None
            if name == "sensitivity":
                caption = "📊 Sensitivity Analysis (What-if Scenario)"

            try:
                with open(image_path, "rb") as img:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=img,
                        caption=caption
                    )
            except FileNotFoundError:
                print(f"[BOT] image not found: {image_path}")

        return  # ⛔ STOP di dict handler

    # =========================
    # 4️⃣ SAFETY NET (UNEXPECTED)
    # =========================
    await update.message.reply_text(
        "Terjadi kesalahan saat memproses permintaan."
    )


def main():
    """
    Bootstrap Telegram Bot
    """
    app = Application.builder().token(
        settings.TELEGRAM_BOT_TOKEN
    ).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, on_message)
    )

    print("🤖 Telegram bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
