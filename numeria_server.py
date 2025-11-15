import os
import logging
import requests
from typing import Optional, Dict, Any

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")

# URL del DataMind (termina en /predict)
DATAMIND_API = os.getenv("DATAMIND_API_URL")

# URL opcional de la mini IA de imágenes (VisualMind)
VISUALMIND_API = os.getenv("VISUALMIND_API_URL", "").strip()

PORT = int(os.getenv("PORT", 10000))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}" if RENDER_URL else ""

# Memoria simple en RAM del último resultado para cada usuario
LAST_RESULT: Dict[int, Dict[str, Any]] = {}

# =========================
# LOGS
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - NumerIA - %(levelname)s - %(message)s",
)
log = logging.getLogger("NumerIA")


# =========================
# HELPERS
# =========================
def call_datamind(texto: str) -> Optional[Dict[str, Any]]:
    if not DATAMIND_API:
        return None

    payload = {
        "query": texto,
        "text": texto,
    }
    r = requests.post(DATAMIND_API, json=payload, timeout=40)
    if r.status_code != 200:
        log.error(f"DataMind respondió {r.status_code}: {r.text}")
        return None
    return r.json()


async def send_visualmind(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Envía la info del último resultado a la mini IA de imágenes (si está configurada)."""
    if not VISUALMIND_API:
        await update.message.reply_text(
            "🖼 Aún no hay una mini IA de imágenes conectada.\n"
            "Cuando VisualMind esté lista, este comando enviará la predicción "
            "para que genere el diseño."
        )
        return

    if not update.effective_user:
        await update.message.reply_text("No pude identificar al usuario.")
        return

    user_id = update.effective_user.id
    last = LAST_RESULT.get(user_id)
    if not last:
        await update.message.reply_text(
            "No tengo una predicción reciente para generar imagen.\n"
            "Primero pide una predicción y luego escribe: imagen"
        )
        return

    try:
        payload = {
            "user_id": user_id,
            "sport": last.get("sport"),
            "match_date": last.get("match_date"),
            "visualmind_payload": last.get("visualmind_payload"),
        }
        r = requests.post(VISUALMIND_API, json=payload, timeout=40)
        if r.status_code != 200:
            log.error(f"VisualMind error {r.status_code}: {r.text}")
            await update.message.reply_text(
                "❌ No pude comunicarme correctamente con la mini IA de imágenes."
            )
            return

        data = r.json()
        msg = data.get("message") or \
            "✅ Petición enviada a la mini IA de imágenes. Revisa el canal donde publiques los creativos."
        await update.message.reply_text(str(msg))

    except Exception as e:
        log.error(f"Error llamando a VisualMind: {e}")
        await update.message.reply_text(
            "❌ Ocurrió un problema al conectar con la mini IA de imágenes."
        )


# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido a NumerIA.\n\n"
        "Envíame el nombre de un partido (ej. 'Liverpool vs City 17/11/2025') "
        "y te daré una predicción con lectura numérica.\n\n"
        "Cuando veas una predicción que te guste, escribe: imagen\n"
        "para mandar esa lectura a la mini IA de creativos (VisualMind) "
        "cuando esté conectada."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Cómo usar NumerIA:\n\n"
        "1️⃣ Escribe el partido o evento, por ejemplo:\n"
        "   • Liverpool vs City 17/11/2025\n"
        "   • Lakers vs Warriors\n"
        "   • Yankees vs Red Sox\n"
        "   • Cowboys vs Eagles\n\n"
        "2️⃣ NumerIA analizará el deporte, números y contexto para darte\n"
        "    una lectura tipo tipster.\n\n"
        "3️⃣ Si quieres generar una imagen para redes de esa predicción,\n"
        "   escribe: imagen\n"
        "   (cuando la mini IA VisualMind esté conectada)."
    )


async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_visualmind(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip()
    log.info(f"📩 Mensaje recibido: {texto}")

    # Si el usuario escribe literalmente "imagen" (sin slash), trata de generar creativos
    if texto.lower() == "imagen":
        await send_visualmind(update, context)
        return

    if not DATAMIND_API:
        await update.message.reply_text(
            "❌ DataMind no está configurado.\n"
            "Configura la variable DATAMIND_API_URL en el panel de Render."
        )
        return

    try:
        pred = call_datamind(texto)
        if not pred:
            await update.message.reply_text(
                "❌ No recibí respuesta válida de DataMind."
            )
            return

        respuesta = pred.get("prediction") or \
            pred.get("message") or \
            "❌ No recibí una predicción válida de DataMind."

        await update.message.reply_text(str(respuesta))

        # Guarda último resultado en memoria temporal por usuario
        if update.effective_user:
            LAST_RESULT[update.effective_user.id] = {
                "sport": pred.get("sport"),
                "match_date": pred.get("match_date"),
                "visualmind_payload": pred.get("visualmind_payload"),
            }

    except Exception as e:
        log.error(f"❌ Error consultando DataMind: {e}")
        await update.message.reply_text(
            "❌ No pude conectarme con DataMind en este momento."
        )


# =========================
# MAIN — Webhook nativo
# =========================
def main():
    log.info("🚀 Iniciando NumerIA con Webhook PTB (sin Flask)")

    if not TOKEN:
        raise RuntimeError("❌ Falta TELEGRAM_TOKEN en variables de entorno.")

    if not WEBHOOK_URL:
        raise RuntimeError(
            "❌ Falta RENDER_EXTERNAL_URL en variables de entorno o no es válida."
        )

    log.info(f"🌐 Webhook final: {WEBHOOK_URL}")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("imagen", image_cmd))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"),
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
