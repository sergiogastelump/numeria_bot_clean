import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import httpx

# ==============================================
# LOGGING
# ==============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("numeria_server")

# ==============================================
# ENV VARIABLES
# ==============================================
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL")

if not DATAMIND_API_URL:
    logger.error("❌ ERROR: DATAMIND_API_URL no está definido.")

# ==============================================
# FLASK APP
# ==============================================
app = Flask(__name__)

# ==============================================
# TELEGRAM APPLICATION
# ==============================================
application = Application.builder().token(BOT_TOKEN).build()
application_initialized = False


async def init_bot():
    """Inicializa PTB evitando loops cerrados."""
    global application_initialized

    if not application_initialized:
        await application.initialize()
        await application.start()
        application_initialized = True
        logger.info("🚀 PTB Application inicializado correctamente.")


# ==============================================
# HANDLERS
# ==============================================
async def cmd_start(update: Update, context):
    await update.message.reply_text(
        "¡Bienvenido a NumerIA! 🔮⚽ Envíame un partido para analizar."
    )


async def handle_message(update: Update, context):
    text = update.message.text
    logger.info(f"Mensaje recibido: {text}")

    # Llamar DataMind con httpx async
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(DATAMIND_API_URL, json={"query": text})
            data = r.json()
    except Exception as e:
        logger.error(f"Error DataMind: {e}")
        data = {"error": "No se pudo conectar a DataMind"}

    respuesta = f"""
📊 *NumerIA - Análisis Deportivo*

🔍 Consulta: *{text}*

📡 DataMind:
`{data}`

⚠️ Respuesta temporal solo de prueba.
"""

    await update.message.reply_text(respuesta, parse_mode="Markdown")


# Registrar handlers
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ==============================================
# WEBHOOK
# ==============================================
@app.route("/webhook", methods=["POST"])
def webhook():

    update_json = request.get_json(force=True, silent=True)
    logger.info("====== UPDATE JSON RECIBIDO ======")
    logger.info(update_json)
    logger.info("==================================")

    if not update_json:
        return "NO JSON", 400

    update = Update.de_json(update_json, application.bot)

    async def process():
        await init_bot()
        await application.process_update(update)

    # EVITAR asyncio.run()
    loop = asyncio.get_event_loop()
    loop.create_task(process())

    return "OK", 200


# ==============================================
# ROOT
# ==============================================
@app.route("/")
def index():
    return "NumerIA Bot Running"


# ==============================================
# RUN SERVER
# ==============================================
if __name__ == "__main__":
    logger.info("Iniciando NumerIA Bot con Flask en puerto 10000")
    app.run(host="0.0.0.0", port=10000)
