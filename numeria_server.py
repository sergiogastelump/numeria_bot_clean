import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

# ==============================================
# CONFIGURACIÓN DE LOGS
# ==============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("numeria_server")


# ==============================================
# CARGA VARIABLES DE ENTORNO
# ==============================================
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL")

if not DATAMIND_API_URL:
    logger.error("❌ ERROR: DATAMIND_API_URL no está definido.")

# ==============================================
# FLASK
# ==============================================
app = Flask(__name__)

# ==============================================
# INICIALIZAR APPLICATION ANTES DEL WEBHOOK
# ==============================================
application = Application.builder().token(BOT_TOKEN).build()
application_initialized = False


async def init_bot():
    """Inicializa el Application ANTES del webhook."""
    global application_initialized
    if not application_initialized:
        await application.initialize()
        await application.start()
        application_initialized = True
        logger.info("🚀 Telegram Application inicializado correctamente.")


# ==============================================
# HANDLERS DEL BOT
# ==============================================
async def cmd_start(update: Update, context):
    await update.message.reply_text("¡Bienvenido a NumerIA! 🔮⚽ Envía un partido para analizar.")


async def handle_message(update: Update, context):
    text = update.message.text
    logger.info(f"Mensaje recibido: {text}")

    # Llamada a DataMind
    try:
        resp = requests.post(DATAMIND_API_URL, json={"query": text})
        data = resp.json()
    except Exception as e:
        data = {"error": "No se pudo conectar a DataMind"}
        logger.error(f"Error DataMind: {e}")

    respuesta = f"""
📊 *NumerIA - Análisis Deportivo*

🔎 Consulta: *{text}*

📡 DataMind:
`{data}`

⚠️ Esto es respuesta temporal solo de prueba.
"""

    await update.message.reply_text(respuesta, parse_mode="Markdown")


# Añadir handlers al Application
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ==============================================
# ENDPOINT DEL WEBHOOK
# ==============================================
@app.route("/webhook", methods=["POST"])
def webhook():
    global application_initialized

    update_json = request.get_json(force=True, silent=True)
    logger.info("====== UPDATE JSON RECIBIDO ======")
    logger.info(update_json)
    logger.info("==================================")

    if not update_json:
        return "No JSON", 400

    update = Update.de_json(update_json, application.bot)

    async def process():
        # Inicializamos el bot ANTES de procesar el update
        await init_bot()
        await application.process_update(update)

    try:
        asyncio.run(process())
    except Exception as e:
        logger.error("❌ Error en webhook:")
        logger.exception(e)

    return "OK", 200


# ==============================================
# ENDPOINT DE PRUEBA
# ==============================================
@app.route("/")
def index():
    return "NumerIA Bot Running"


# ==============================================
# EJECUCIÓN
# ==============================================
if __name__ == "__main__":
    logger.info("Iniciando NumerIA Bot con Flask en puerto 10000")
    app.run(host="0.0.0.0", port=10000)
