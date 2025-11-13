import os
import json
import asyncio
import logging
import requests
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# =====================
# CONFIGURACIÓN BÁSICA
# =====================
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL", "https://numeria-datamind-eykx.onrender.com/predict")

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("numeria-server")

# =====================
# HANDLERS DE TELEGRAM
# =====================
telegram_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, soy NumerIA. Envíame un código o mensaje para analizarlo con DataMind.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Mensaje inicial
    await update.message.reply_text("⏳ Analizando tu mensaje...")

    # Petición a DataMind
    try:
        payload = {"user": user_name, "text": user_text}
        headers = {"Content-Type": "application/json"}
        response = requests.post(DATAMIND_API_URL, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            result = data.get("interpretation", "No se obtuvo respuesta de DataMind.")
            await context.bot.send_message(chat_id=chat_id, text=f"🧠 {result}")
        else:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Error en DataMind (no disponible).")

    except Exception as e:
        logger.exception("Error comunicando con DataMind")
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error interno: {e}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# =====================
# RUTAS FLASK
# =====================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ NumerIA activo con DataMind IA"}), 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        asyncio.run(telegram_app.process_update(update))
    except Exception as e:
        logger.exception("Error procesando update")
    return "OK", 200

@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    try:
        url = f"https://numeria-bot-v2.onrender.com/{TOKEN}"
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook", params={"url": url})
        return jsonify(r.json()), 200
    except Exception as e:
        logger.exception("Error configurando webhook")
        return jsonify({"error": str(e)}), 500

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
