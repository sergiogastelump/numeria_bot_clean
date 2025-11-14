import os
import logging
import json
import requests
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API = os.getenv("DATAMIND_API_URL")

PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_URL')}/webhook"

# =========================
# LOGS
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("NumerIA")

# =========================
# Handlers
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Bienvenido a NumerIA!\n"
        "Envíame el nombre de un partido y te doy la predicción numerológica."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    log.info(f"📩 Mensaje recibido: {texto}")

    if not DATAMIND_API:
        await update.message.reply_text("❌ DataMind no está configurado.")
        return

    try:
        r = requests.post(
            DATAMIND_API,
            json={"text": texto},
            timeout=20
        )

        pred = r.json()
        respuesta = pred.get("prediction", "❌ Error al procesar la predicción")

    except Exception as e:
        log.error(f"Error consultando Datamind: {e}")
        respuesta = "❌ No pude obtener datos de DataMind."

    await update.message.reply_text(respuesta)

# =========================
# MAIN — Webhook nativo
# =========================
def main():
    log.info("🚀 Iniciando NumerIA con Webhook PTB (sin Flask)")

    if not TOKEN:
        raise RuntimeError("❌ Falta TELEGRAM_TOKEN en variables!")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    log.info(f"🌐 Configurando webhook: {WEBHOOK_URL}")

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
