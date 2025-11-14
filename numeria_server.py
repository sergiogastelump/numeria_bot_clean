import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
import requests


# ==============================
# CONFIGURACIÓN INICIAL
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("numeria_server")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL")

if not TELEGRAM_TOKEN:
    logger.error("❌ ERROR: TELEGRAM_TOKEN no está configurado en Render.")

if not DATAMIND_API_URL:
    logger.error("❌ ERROR: DATAMIND_API_URL no está configurado en Render.")

bot = Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)


# ==============================
# HANDLERS DEL BOT
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Bienvenido a NumerIA!\n\n"
        "Envíame el nombre de un partido y te daré el análisis numerológico + deportivo automático."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja cualquier texto enviado por el usuario."""
    user_text = update.message.text.strip()
    logger.info(f"Mensaje recibido: {user_text}")

    # Llamada a DataMind
    try:
        r = requests.post(DATAMIND_API_URL, json={"query": user_text})
        r.raise_for_status()
        data = r.json()
        respuesta = data.get("response", "⚠️ No se pudo interpretar la respuesta del servidor.")
    except Exception as e:
        logger.error(f"Error DataMind: {e}")
        respuesta = "⚠️ Hubo un problema consultando el motor de predicción."

    await update.message.reply_text(respuesta, parse_mode="Markdown")


# ==============================
# INICIALIZACIÓN DEL BOT
# ==============================

application = Application.builder().token(TELEGRAM_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ==============================
# INICIALIZAR TELEGRAM APP UNA SOLA VEZ
# ==============================

async def start_application():
    """Se ejecuta solo al iniciar, NO por cada webhook."""
    await application.initialize()
    await application.start()
    logger.info("🚀 Telegram Application inicializado correctamente.")


# Creamos loop principal (Render lo soporta)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_application())


# ==============================
# WEBHOOK (procesado correcto)
# ==============================

@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe updates de Telegram y los envía a la cola interna de PTB."""
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            return jsonify({"status": "no json"}), 200

        logger.info("====== UPDATE JSON RECIBIDO ======")
        logger.info(data)
        logger.info("==================================")

        update = Update.de_json(data, bot)

        # Enviar update a la cola interna del bot
        application.update_queue.put_nowait(update)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}", exc_info=True)
        return jsonify({"status": "error"}), 200


@app.route("/", methods=["GET"])
def home():
    return "NumerIA Bot está activo ✔️", 200


# ==============================
# EJECUCIÓN FLASK
# ==============================

if __name__ == "__main__":
    logger.info("Iniciando NumerIA Bot con Flask en puerto 10000")
    app.run(host="0.0.0.0", port=10000)
