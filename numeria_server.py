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
    filters,
)

# Motores internos de NumerIA
from modules.predict_engine import generate_numeria_response

# -------------------------------------------------
# Configuración básica
# -------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno.")

WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))

# -------------------------------------------------
# Inicializar Application de python-telegram-bot 21.x
# -------------------------------------------------
application = Application.builder().token(TELEGRAM_TOKEN).build()

# -------------------------------------------------
# Handlers de comandos
# -------------------------------------------------
WELCOME_TEXT = (
    "👋 Bienvenido a *NumerIA Tipster*.\n\n"
    "Envíame un partido o enfrentamiento, por ejemplo:\n"
    "• `Liverpool vs City`\n"
    "• `Lakers vs Celtics`\n"
    "• `Yankees vs Red Sox`\n"
    "• `Cowboys vs Eagles`\n\n"
    "Y recibirás una lectura con:\n"
    "• Datos reales (DataMind)\n"
    "• Análisis numérico (numerología técnica + gematría)\n"
    "• Interpretación estilo tipster profesional\n\n"
    "_Aviso: NumerIA es una guía avanzada, no garantiza resultados._"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start."""
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help."""
    text = (
        "ℹ️ *Ayuda NumerIA*\n\n"
        "Solo envía el partido o enfrentamiento que quieras analizar.\n\n"
        "Ejemplos:\n"
        "• `Liverpool vs City`\n"
        "• `Real Madrid vs Barcelona`\n"
        "• `Yankees vs Dodgers`\n"
        "• `Lakers vs Warriors`\n\n"
        "También funciona con texto más libre, pero el formato 'Equipo vs Equipo' "
        "es el más recomendado para análisis completo."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# -------------------------------------------------
# Handler principal de mensajes de texto
# -------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa cualquier mensaje de texto que no sea comando."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text.strip()
    logger.info("Mensaje de %s (%s): %s", user.first_name, user.id, text)

    try:
        reply_text = generate_numeria_response(text)
    except Exception as e:
        logger.exception("Error generando respuesta NumerIA: %s", e)
        reply_text = (
            "⚠️ Ocurrió un error interno generando la lectura.\n"
            "Intenta de nuevo con otro partido o en unos momentos."
        )

    await update.message.reply_text(reply_text, parse_mode="Markdown")


# Registrar handlers en la Application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# -------------------------------------------------
# Flask + Webhook
# -------------------------------------------------
app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "NumerIA Bot funcionando correctamente.", 200


@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    """Endpoint que recibe las actualizaciones de Telegram."""
    try:
        data = request.get_json(force=True, silent=True)
    except Exception:
        return "Bad Request", 400

    if not data:
        return "No data", 400

    update = Update.de_json(data, application.bot)

    async def process_update():
    try:
        # Intentamos inicializar la aplicación (si ya lo estaba, no pasa nada)
        await application.initialize()
    except Exception:
        pass

    try:
        # Intentamos arrancar la aplicación (si ya está corriendo, no pasa nada)
        await application.start()
    except Exception:
        pass

    # Ahora sí procesamos el update
    await application.process_update(update)


    try:
        asyncio.run(process_update())
    except RuntimeError as e:
        # Por si hubiera conflicto de event loop, intentamos crear uno nuevo
        logger.error("Error procesando update: %s", e)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update())
        finally:
            asyncio.set_event_loop(None)

    return "OK", 200


# -------------------------------------------------
# Main local (en Render solo levanta Flask)
# -------------------------------------------------
if __name__ == "__main__":
    # Webhook local/manual opcional (no necesario en Render si ya lo configuraste desde BotFather)
    # Solo por si quieres probar en otro entorno.
    logger.info("Iniciando NumerIA Bot con Flask en puerto %s", PORT)
    app.run(host="0.0.0.0", port=PORT)
