import os
import asyncio
import logging
import requests
from flask import Flask, request

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Motores internos NumerIA
from modules.predict_engine import generate_numeria_response

# ----------------------------------------------------------
# LOGGING
# ----------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("numeria_server")

# ----------------------------------------------------------
# VARS
# ----------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ Falta TELEGRAM_TOKEN en variables de entorno.")

DATAMIND_URL = os.getenv("DATAMIND_URL")

WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))

# ----------------------------------------------------------
# Telegram Application (PTB 21.4)
# ----------------------------------------------------------
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ----------------------------------------------------------
# HANDLERS
# ----------------------------------------------------------

WELCOME_MSG = (
    "👋 Bienvenido a *NumerIA Tipster*.\n\n"
    "Envíame un partido, ejemplo:\n"
    "• Liverpool vs City\n"
    "• Lakers vs Celtics\n"
    "• Yankees vs Red Sox\n\n"
    "Obtendrás:\n"
    "• Estadística DataMind\n"
    "• Análisis numérico\n"
    "• Pick final estilo tipster profesional\n\n"
    "_Ningún modelo garantiza resultados._"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MSG, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Envíame: Equipo1 vs Equipo2\n\n"
        "Ejemplos:\n"
        "• América vs Chivas\n"
        "• Real Madrid vs Barcelona\n"
        "• Dodgers vs Giants\n",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa cualquier texto que no sea comando."""
    if not update.message:
        return

    user_text = update.message.text.strip()
    user = update.effective_user
    logger.info("Mensaje de %s (%s): %s", user.first_name, user.id, user_text)

    try:
        response = generate_numeria_response(user_text)
    except Exception as e:
        logger.exception("Error generando respuesta NumerIA: %s", e)
        response = "⚠️ Ocurrió un error analizando el partido. Intenta nuevamente."

    await update.message.reply_text(response, parse_mode="Markdown")

# Registrar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

# ----------------------------------------------------------
# FLASK SERVER + WEBHOOK
# ----------------------------------------------------------
app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "NumerIA Bot funcionando correctamente.", 200


@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    """Endpoint que recibe actualizaciones de Telegram."""
    data = request.get_json(silent=True)

    if not data:
        return "No data", 400

    update = Update.de_json(data, application.bot)

    async def process_update():
        # Intentar inicializar (si ya está inicializado no pasa nada)
        try:
            await application.initialize()
        except Exception:
            pass

        # Intentar arrancar (si ya estaba arrancado no pasa nada)
        try:
            await application.start()
        except Exception:
            pass

        # Procesar update
        await application.process_update(update)

    try:
        asyncio.run(process_update())
    except RuntimeError:
        # Si ya existe otro event loop, creamos uno nuevo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_update())
        asyncio.set_event_loop(None)

    return "OK", 200


# ----------------------------------------------------------
# MAIN (solo para ejecución local)
# ----------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"Iniciando NumerIA Bot con Flask en puerto {PORT}")
    app.run(host="0.0.0.0", port=PORT)
