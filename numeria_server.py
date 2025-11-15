import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API = os.getenv("DATAMIND_API_URL")  # Debe apuntar a /predict

PORT = int(os.getenv("PORT", 10000))

# Render ya DA la URL COMPLETA con https://
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}" if RENDER_URL else ""

# =========================
# LOGS
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("NumerIA")


# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Bienvenido a NumerIA!\n"
        "Envíame el nombre de un partido y te doy la predicción numerológica."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip()
    log.info(f"📩 Mensaje recibido: {texto}")

    if not DATAMIND_API:
        await update.message.reply_text("❌ DataMind no está configurado.")
        return

    # Payload compatible: envía tanto query como text
    payload = {
        "query": texto,
        "text": texto,
    }

    try:
        r = requests.post(DATAMIND_API, json=payload, timeout=20)

        if r.status_code != 200:
            log.error(f"❌ DataMind respondió {r.status_code}: {r.text}")
            await update.message.reply_text(
                "❌ DataMind no respondió correctamente. Intenta de nuevo más tarde."
            )
            return

        pred = r.json()

    except Exception as e:
        log.error(f"❌ Error consultando DataMind: {e}")
        await update.message.reply_text(
            "❌ No pude conectarme con DataMind en este momento."
        )
        return

    # Toma primero 'prediction', si no, algún mensaje alterno
    respuesta = (
        pred.get("prediction")
        or pred.get("message")
        or "❌ No recibí una predicción válida de DataMind."
    )

    await update.message.reply_text(str(respuesta))


# =========================
# MAIN — Webhook nativo
# =========================
def main():
    log.info("🚀 Iniciando NumerIA con Webhook PTB (sin Flask)")

    if not TOKEN:
        raise RuntimeError("❌ Falta TELEGRAM_TOKEN en variables de entorno.")

    if not WEBHOOK_URL:
        raise RuntimeError(
            "❌ Falta RENDER_EXTERNAL_URL en variables de entorno "
            "o no es válida."
        )

    log.info(f"🌐 Webhook final: {WEBHOOK_URL}")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"),  # "webhook"
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
