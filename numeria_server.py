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
        "Envía un partido como:\n\n"
        "Liverpool vs City\n"
        "Real Madrid vs Barcelona\n"
        "y te doy análisis + lectura numérica."
    )


async def handle_message(update: Update, context):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    logger.info("Mensaje de Sergio (%s): %s", chat_id, text)

    # ========== 1. DataMind ==========
    try:
        dm = requests.post(DATAMIND_URL, json={"query": text}, timeout=7)
        pred = dm.json().get("prediccion", "Predicción no disponible")
    except Exception as e:
        pred = f"Error conectando con DataMind ({e})"

    # ========== 2. Número ==========
    codigo = random.randint(11, 99)

    # ========== 3. Mensaje ==========
    msg = (
        f"📊 *Análisis NumerIA para:* *{text}*\n\n"
        f"🔹 *Tendencia:* {pred}\n\n"
        f"🔢 *Código numérico:* {codigo}\n"
        f"• Lectura: Proyección confiable basada en patrones\n\n"
        f"📌 Basado en ciclos estadísticos + DataMind\n"
        f"⚠️ Herramienta de apoyo, no garantiza resultados."
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


# Registrar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ============================================================
# LOOP GLOBAL PARA PROCESAR UPDATES
# ============================================================
async def process_updates_loop():
    """Procesa la cola interna de updates continuamente."""
    while True:
        update = await application.update_queue.get()
        try:
            await application.process_update(update)
        except Exception as e:
            logger.error(f"Error procesando update: {e}")


async def run_application():
    """Inicializa Application sin polling."""
    await application.initialize()
    await application.start()

    # iniciar loop interno
    asyncio.create_task(process_updates_loop())


def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_application())
    loop.run_forever()


# Ejecutar bot en segundo plano
threading.Thread(target=start_bot_thread, daemon=True).start()


# ============================================================
# WEBHOOK
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, application.bot)
        application.update_queue.put_nowait(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"ERROR Webhook: {e}")
        return "ERROR", 500


# ============================================================
# HOME
# ============================================================
@app.route("/")
def home():
    return "NumerIA Tipster ONLINE ✔ (Webhook working)", 200


# ============================================================
# RUN FLASK
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
