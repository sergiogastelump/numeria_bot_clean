import os
import logging
import threading
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import random

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
# FLASK SERVER
# ============================================================
app = Flask(__name__)
logger.info("Iniciando NumerIA Bot con Flask en puerto %s", PORT)

# ============================================================
# TELEGRAM APPLICATION (PTB 21) — UNA SOLA VEZ
# ============================================================
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ============================================================
# HANDLERS
# ============================================================
async def start(update: Update, context):
    await update.message.reply_text(
        "¡Bienvenido a NumerIA Tipster! 🔮📊\n"
        "Escribe un partido como:\n\n"
        "Liverpool vs City\n"
        "Real Madrid vs Barcelona\n"
        "Y te daré análisis + lectura numérica."
    )

async def handle_message(update: Update, context):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    logger.info("Mensaje de Sergio (%s): %s", chat_id, text)

    # 1. DataMind
    try:
        resp = requests.post(DATAMIND_URL, json={"query": text}, timeout=6)
        pred = resp.json().get("prediccion", "No disponible")
    except:
        pred = "Error conectando con DataMind."

    # 2. Código numérico
    codigo = random.randint(11, 99)

    # 3. Respuesta
    msg = (
        f"📊 *Análisis NumerIA para:* *{text}*\n\n"
        f"🔹 *Tendencia:* {pred}\n\n"
        f"🔢 *Cálculo numérico*\n"
        f"• Código: *{codigo}*\n"
        f"• Lectura: Proyección equilibrada\n\n"
        f"📌 Basado en patrones numéricos + DataMind\n"
        f"⚠️ Herramienta de apoyo, no garantiza resultados."
    )

    await update.message.reply_text(msg, parse_mode="Markdown")

# Registrar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ============================================================
# RUNNER ASYNC SIN POLLING (WEBHOOK MODE)
# ============================================================

async def run_application():
    await application.initialize()
    await application.start()

def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_application())
    loop.run_forever()

threading.Thread(target=start_bot_thread, daemon=True).start()

# ============================================================
# WEBHOOK
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)

        # Enviar update al queue interno de PTB
        application.update_queue.put_nowait(update)

        return "OK", 200

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return "ERROR", 500

# ============================================================
# HOME
# ============================================================
@app.route("/")
def home():
    return "NumerIA Bot ONLINE ✔ (Webhook Mode)", 200

# ============================================================
# RUN FLASK
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
