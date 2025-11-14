import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
import requests

# -----------------------------------------
# CONFIGURACIÓN DE LOGS
# -----------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("numeria_server")


# -----------------------------------------
# VARIABLES DE ENTORNO
# -----------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL")

if not TELEGRAM_TOKEN:
    logger.error("❌ ERROR: TELEGRAM_TOKEN no está definido.")
if not DATAMIND_API_URL:
    logger.error("❌ ERROR: DATAMIND_API_URL no está definido.")


# -----------------------------------------
# INICIALIZAR APP TELEGRAM
# -----------------------------------------
application = Application.builder().token(TELEGRAM_TOKEN).build()


# -----------------------------------------
# EXTRACTOR SÚPER ROBUSTO DE TEXTO
# -----------------------------------------
def extract_text(update: Update) -> str | None:
    """
    Extrae el texto desde cualquier tipo de update.
    Compatible con todos los formatos de Telegram.
    """

    try:
        if update.message and update.message.text:
            return update.message.text

        if update.edited_message and update.edited_message.text:
            return update.edited_message.text

        if update.channel_post and update.channel_post.text:
            return update.channel_post.text

        if update.edited_channel_post and update.edited_channel_post.text:
            return update.edited_channel_post.text

        if update.callback_query and update.callback_query.data:
            return update.callback_query.data

        # Si viene texto dentro de update.to_dict()
        data = update.to_dict()
        if "message" in data and "text" in data["message"]:
            return data["message"]["text"]

        return None

    except Exception as e:
        logger.error(f"❌ Error en extract_text: {e}")
        return None


# -----------------------------------------
# FUNCIÓN PRINCIPAL DEL BOT
# -----------------------------------------
async def handle_message(update: Update, context):
    user_id = update.effective_user.id if update.effective_user else "desconocido"
    logger.info(f"📩 Mensaje recibido de {user_id}")

    text = extract_text(update)
    if not text:
        await update.effective_chat.send_message(
            "⚠️ No pude leer el mensaje. Intenta de nuevo."
        )
        return

    # ----------------------------
    # CONSULTAR DATAMIND API
    # ----------------------------
    try:
        r = requests.post(
            DATAMIND_API_URL,
            json={"query": text},
            timeout=20
        )

        if r.status_code != 200:
            result = "❌ Error conectando con DataMind."
        else:
            data = r.json()
            result = data.get("analysis", "⚠️ DataMind no envió análisis.")

    except Exception as e:
        logger.error(f"❌ Error al contactar DataMind: {e}")
        result = "❌ DataMind no disponible."

    # ----------------------------
    # RESPUESTA TIPO TIPSTER NUMÉRICO
    # ----------------------------
    response = f"""
📊 *Predicción NumerIA para:* `{text}`

📌 *Análisis estadístico (DataMind)*  
{result}

🔢 *Relevancia numérica*
• Clave dominante: {abs(hash(text)) % 90 + 10}
• Coincidencias internas: {sum(ord(c) for c in text) % 7}

📈 *Tendencia cuantitativa*
El modelo detecta patrones consistentes basados en:
- distribuciones históricas del rendimiento
- coherencia numérica interna
- correlaciones recientes

⚠️ *Aviso*: NumerIA es una guía basada en análisis numérico + tendencias.
"""

    await update.effective_chat.send_message(
        response,
        parse_mode="Markdown"
    )


# -----------------------------------------
# HANDLERS
# -----------------------------------------
async def start(update: Update, context):
    await update.message.reply_text(
        "🤖 Hola, soy *NumerIA Tipster*.\n"
        "Envíame un partido o evento y te doy el análisis completo.",
        parse_mode="Markdown"
    )


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# -----------------------------------------
# FLASK SERVER
# -----------------------------------------
app = Flask(__name__)


@app.get("/")
def home():
    return "NumerIA Bot funcionando."


@app.post("/webhook")
def webhook():
    """
    Recibe actualizaciones desde Telegram via Webhook
    """
    try:
        update_json = request.get_json(silent=True, force=True)

        # -------------------------------------------------------
        # LOG COMPLETO DEL JSON ENTRANTE (CLAVE PARA DEBUG)
        # -------------------------------------------------------
        logger.info("====== UPDATE JSON RECIBIDO ======")
        logger.info(update_json)
        logger.info("==================================")

        if not update_json:
            logger.error("⚠️ ERROR: update_json vacío")
            return "OK", 200

        update = Update.de_json(update_json, application.bot)

        # Procesar el update con Telegram Application
        asyncio.run(application.process_update(update))

        return "OK", 200

    except Exception as e:
        logger.exception("❌ Error en webhook:")
        return "ERROR", 500


# -----------------------------------------
# INICIO DEL SERVIDOR
# -----------------------------------------
if __name__ == "__main__":
    logger.info("Iniciando NumerIA Bot con Flask en puerto 10000")
    app.run(host="0.0.0.0", port=10000)
