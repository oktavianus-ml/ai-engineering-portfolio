import requests
from app.config.settings import settings


def handle_message(text: str, chat_id: int):
    payload = {
        "message": text,
        "chat_id": chat_id,
        "source": "telegram",
    }

    # =========================
    # CALL BACKEND
    # =========================
    try:
        response = requests.post(
            settings.FASTAPI_CHAT_URL,
            json=payload,
            timeout=30,
        )
    except requests.Timeout:
        return [{
            "type": "text",
            "value": "⏳ Server sedang sibuk. Coba lagi sebentar."
        }]
    except requests.ConnectionError:
        return [{
            "type": "text",
            "value": "⚠️ Tidak dapat terhubung ke server."
        }]
    except requests.RequestException as e:
        print("[TELEGRAM_HANDLER] Request error:", e)
        return [{
            "type": "text",
            "value": "⚠️ Terjadi kesalahan jaringan."
        }]

    if response.status_code != 200:
        return [{
            "type": "text",
            "value": "⚠️ Terjadi kesalahan di sistem. Silakan coba lagi."
        }]

    # =========================
    # PARSE JSON
    # =========================
    try:
        data = response.json()
    except ValueError:
        return [{
            "type": "text",
            "value": "⚠️ Respon backend tidak valid."
        }]

    reply = data.get("response")

    if reply is None:
        return [{
            "type": "text",
            "value": "⚠️ Backend tidak mengirim response."
        }]

    messages = []

    # =========================
    # STRING RESPONSE
    # =========================
    if isinstance(reply, str):
        messages.append({
            "type": "text",
            "value": reply
        })
        return messages

    # =========================
    # DICT RESPONSE
    # =========================
    if isinstance(reply, dict):

        # text
        if reply.get("text"):
            messages.append({
                "type": "text",
                "value": reply["text"]
            })

        # single image (legacy)
        if reply.get("image"):
            messages.append({
                "type": "image",
                "value": reply["image"],
                "caption": "📈 Forecast"
            })

        # multi images
        images = reply.get("images", {})
        if isinstance(images, dict):
            if images.get("weekly"):
                messages.append({
                    "type": "image",
                    "value": images["weekly"],
                    "caption": "📈 Weekly Forecast"
                })
            if images.get("monthly"):
                messages.append({
                    "type": "image",
                    "value": images["monthly"],
                    "caption": "📊 Monthly Forecast"
                })
            if images.get("yearly"):
                messages.append({
                    "type": "image",
                    "value": images["yearly"],
                    "caption": "🧭 Yearly Forecast"
                })

        if messages:
            return messages

    # =========================
    # FALLBACK
    # =========================
    return [{
        "type": "text",
        "value": "⚠️ Format response tidak dikenali."
    }]