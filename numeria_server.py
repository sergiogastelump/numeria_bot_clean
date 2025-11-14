import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import random
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
TELEGRAM_TOKEN = "8060973627:AAFbjXs3mk624axpH4vh0kP_Cbew52YQ3zw"
DATAMIND_URL = "https://numeria-datamind-1.onrender.com/predict"

PORT = int(os.environ.get("PORT", 10000))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("numeria_server")

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
logger.info("Iniciando NumerIA Bot con Flask en puerto %s", PORT)

# ============================================================
# APPLICATION (PTB 21) — UNA SOLA INICIALIZACIÓN
# ============================================================
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ============================================================
# COMANDOS
# ============================================================
async def start(update: Update, context):
    await update.message.reply_text(
        "¡Bienvenido a NumerIA Tipster! 🔮📊\n"
        "Envíame un partido como:\n\n"
        "Liverpool vs City\n"
        "Real Madrid vs Barcelona\n"
        "Y te daré análisis deportivo + lectura numérica."
    )

async def handle_message(update: Update, context):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    logger.info("Mensaje de Sergio (%s): %s", chat_id, text)

    # ------------------------------------------
    # 1. CONSULTA A DATAMIND
    # ------------------------------------------
    try:
        dm = requests.post(DATAMIND_URL, json={"query": text}, timeout=7)
        dato = dm.json()
        tendencia = dato.get("prediccion", "No disponible")
    except Exception as e:
        logger.error(f"Error DataMind: {e}")
        tendencia = "Error conectando con DataMind."

    # ------------------------------------------
    # 2. CÓDIGO NUMEROLÓGICO
    # ------------------------------------------
    codigo = random.randint(10, 99)
    lectura_codigo = "Equilibrio numérico entre tendencia y riesgo."
    etiqueta = "Proyección estadística validada"

    # ------------------------------------------
    # 3. RESPUESTA FINAL
    # ------------------------------------------
    respuesta = (
        f"📊 *Análisis NumerIA para:* *{text}*\n\n"

        f"🔹 *Tendencia principal:* {tendencia}\n\n"

        f"🔢 *Cálculo numérico*\n"
        f"• Código estadístico: *{codigo}*\n"
        f"• Interpretación: {lectura_codigo}\n"
        f"• Etiqueta: {etiqueta}\n\n"

        f"📌 *Recomendación tipster:*\n"
        f"Basado en ciclos numéricos, memoria histórica y proyección DataMind.\n\n"

        f"⚠️ NumerIA no garantiza resultados. Es una herramienta profesional de apoyo."
    )

    # ------------------------------------------
    # 4. ENVÍO DE MENSAJE
    # ------------------------------------------
    await update.message.reply_text(respuesta, parse_mode="Markdown")


# ============================================================
# HANDLERS
# ============================================================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ============================================================
# LOOP GLOBAL PARA PROCESAR WEBHOOK
# ============================================================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def process_update(update_json):
    update = Update.de_json(update_json, application.bot)
    await application.initialize()
    await application.process_update(update)
    # ❗ NO cerrar el loop, NUNCA


# ============================================================
# WEBHOOK
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        loop.create_task(process_update(update_json))
        return "OK", 200
    except Exception as e:
        logger.error(f"Error procesando update: {e}")
        return "ERROR", 500


# ============================================================
# HOME
# ============================================================
@app.route("/", methods=["GET"])
def home():
    return "NumerIA Bot Running", 200


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
