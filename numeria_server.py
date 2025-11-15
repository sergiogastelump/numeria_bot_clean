import os
import logging
import asyncio
import aiohttp
import requests
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API = os.getenv("DATAMIND_API_URL")
PORT = int(os.getenv("PORT", 10000))

RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}" if RENDER_URL else None

# =========================
# LOGS
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("NumerIA")


# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido a NumerIA.\n\n"
        "Envíame el nombre de un partido (ej. 'Liverpool vs City 20/11/2025') "
        "y te daré una predicción con lectura numérica.\n\n"
        "Cuando veas una predicción que te guste, escribe: imagen "
        "para enviarla a VisualMind."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    log.info(f"📩 Mensaje recibido: {texto}")

    if not DATAMIND_API:
        return await update.message.reply_text("❌ DataMind no está configurado.")

    payload = {"query": texto, "text": texto}

    try:
        r = requests.post(DATAMIND_API, json=payload, timeout=25)
        if r.status_code != 200:
            log.error(f"DataMind error: {r.text}")
            return await update.message.reply_text("❌ Error consultando DataMind.")

        pred = r.json()

    except Exception as e:
        log.error(f"DataMind FAIL: {e}")
        return await update.message.reply_text("❌ No pude conectarme con DataMind.")

    respuesta = pred.get("prediction") or pred.get("message") or "❌ Error interno."
    await update.message.reply_text(respuesta)


# =========================
# WEBHOOK INIT
# =========================
async def post_init(application: Application):
    log.info(f"🌐 Registrando webhook: {WEBHOOK_URL}")
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=WEBHOOK_URL)


# =========================
# KEEP ALIVE (mantiene DataMind vivo)
# =========================
async def keep_alive():
    log.info("🟢 KeepAlive iniciado (ping cada 50 segundos)")

    base_url = DATAMIND_API.replace("/predict", "") if DATAMIND_API else None
    if not base_url:
        log.error("❌ KeepAlive no pudo iniciar: DATAMIND_API_URL no encontrado")
        return

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as resp:
                    log.info(f"Ping DataMind → {resp.status}")
        except Exception as e:
            log.error(f"KeepAlive error: {e}")

        await asyncio.sleep(50)  # Render FREE se duerme al minuto → 50s es perfecto.


# =========================
# MAIN (Webhooks + Gunicorn)
# =========================
application = Application.builder().token(TOKEN).post_init(post_init).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)


def run():
    log.info("🚀 NumerIA iniciado (Render + Gunicorn + KeepAlive)")

    # Ejecutar keep alive
    application.create_task(keep_alive())

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"),
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    run()
