import os
import asyncio
import logging
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

# -------------------------------------------------
# CONFIGURACIÓN BÁSICA
# -------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno.")

DATAMIND_URL = os.getenv("DATAMIND_URL", "https://numeria-datamind.onrender.com/predict")

premium_env = os.getenv("PREMIUM_USERS", "").strip()
PREMIUM_USERS = set(
    uid.strip() for uid in premium_env.split(",") if uid.strip().isdigit()
)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()


# -------------------------------------------------
# FUNCIONES NÚCLEO: CÓDIGOS DE PODER, INTERPRETACIÓN, TIPSTER
# -------------------------------------------------
def calcular_codigo_poder(texto: str) -> dict:
    limpio = "".join(ch for ch in texto.lower() if ch.isalnum())
    if not limpio:
        base = 7
    else:
        base = sum(ord(ch) for ch in limpio) % 99 + 1

    if base <= 22:
        arquetipo = "Inicio y construcción"
        mensaje = "Energía ideal para comenzar retos, construir bank y tomar decisiones calculadas."
    elif base <= 44:
        arquetipo = "Expansión y goles"
        mensaje = "Energía ofensiva, propicia para marcadores con goles y tendencias over."
    elif base <= 66:
        arquetipo = "Equilibrio y cautela"
        mensaje = "Energía de control: ideal para mercados más seguros o combinaciones moderadas."
    elif base <= 88:
        arquetipo = "Riesgo inteligente"
        mensaje = "Energía de apuesta valiente pero con plan, perfecta para buscar cuotas más altas."
    else:
        arquetipo = "Transformación total"
        mensaje = "Energía de giros inesperados, ideal para sorpresas y handicaps creativos."

    return {
        "codigo": base,
        "arquetipo": arquetipo,
        "mensaje": mensaje,
    }


def extraer_info_datamind(data: dict | None) -> dict:
    if not isinstance(data, dict):
        return {
            "bruto": str(data),
            "prediccion": "Sin formato reconocido.",
            "confianza": None,
            "mercado": None,
            "extra": {},
        }

    pred = (
        data.get("prediction")
        or data.get("prediccion")
        or data.get("result")
        or data.get("resultado")
        or "No se encontró una predicción clara."
    )

    conf = data.get("confidence") or data.get("confianza")
    mercado = data.get("market") or data.get("mercado")

    extra = {
        k: v
        for k, v in data.items()
        if k not in {"prediction", "prediccion", "result", "resultado", "confidence", "confianza", "market", "mercado"}
    }

    return {
        "bruto": data,
        "prediccion": pred,
        "confianza": conf,
        "mercado": mercado,
        "extra": extra,
    }


def construir_mensaje_tipster(
    consulta_usuario: str,
    info_dm: dict | None,
    info_codigo: dict,
    es_premium: bool,
) -> str:

    base = extraer_info_datamind(info_dm)

    titulo = f"🔥 *Lectura NumerIA* para: _{consulta_usuario}_\n\n"

    bloque_deportivo = "📊 *Análisis deportivo*\n"
    bloque_deportivo += f"• Tendencia principal: *{base['prediccion']}*\n"

    if base["mercado"]:
        bloque_deportivo += f"• Mercado sugerido: `{base['mercado']}`\n"

    if base["confianza"] is not None:
        try:
            conf_pct = float(base["confianza"]) * 100 if float(base["confianza"]) <= 1 else float(base["confianza"])
            bloque_deportivo += f"• Confianza modelo: *{conf_pct:.1f}%*\n"
        except:
            bloque_deportivo += f"• Confianza modelo: *{base['confianza']}*\n"

    bloque_poder = "🔮 *Código de poder NumerIA*\n"
    bloque_poder += f"• Código: *{info_codigo['codigo']}*\n"
    bloque_poder += f"• Arquetipo: _{info_codigo['arquetipo']}_\n"
    bloque_poder += f"• Lectura: {info_codigo['mensaje']}\n\n"

    if es_premium:
        bloque_premium = "💎 *Modo Premium activo*\n"
        bloque_premium += "• Recomendación avanzada: combina lectura con stake fijo o gradual según tu reto.\n"
        bloque_premium += "• Enfoque sugerido: mercados coherentes con la tendencia y energía del partido.\n"
    else:
        bloque_premium = "🆓 *Modo Free*\n"
        bloque_premium += "Lectura base completa. Para escenarios alternos y gestión de bank avanzada,\n"
        bloque_premium += "puedes activar Premium más adelante.\n"

    cierre = "\n⚠️ *Aviso*: NumerIA es una guía inteligente, no garantiza resultados."

    return titulo + bloque_deportivo + "\n" + bloque_poder + bloque_premium + cierre


# -------------------------------------------------
# HANDLERS
# -------------------------------------------------
async def start(update: Update, context):
    user = update.effective_user
    es_premium = str(user.id) in PREMIUM_USERS

    mensaje = (
        f"Hola {user.first_name or ''}, soy *NumerIA* 🤖✨\n\n"
        "Tu asistente tipster IA personal.\n\n"
        "Envíame:\n"
        "• Un partido (ej: `Liverpool vs City`)\n"
        "• Una liga + pick (ej: `Serie A over 2.5`)\n"
        "• O un código (ej: `COD 27`)\n"
        "y te daré una lectura numérica + deportiva.\n\n"
    )

    if es_premium:
        mensaje += "💎 *Premium activado.*\n"
    else:
        mensaje += "🆓 Modo Free activo.\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def help_command(update: Update, context):
    texto = (
        "ℹ️ *Ayuda NumerIA*\n\n"
        "Solo envía el partido o código que quieras analizar.\n"
        "Ejemplos:\n"
        "• `Real Madrid vs Barça`\n"
        "• `Napoli over 2.5`\n"
        "• `COD 33`\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def handle_message(update: Update, context):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip()
    user = update.effective_user
    user_id = str(user.id)
    es_premium = user_id in PREMIUM_USERS

    logger.info("Mensaje de %s (%s): %s", user.first_name, user_id, texto)

    info_codigo = calcular_codigo_poder(texto)

    info_dm = None
    try:
        resp = requests.post(DATAMIND_URL, json={"input": texto}, timeout=12)
        if resp.status_code == 200:
            try:
                info_dm = resp.json()
            except:
                info_dm = {"prediction": resp.text}
        else:
            info_dm = {"prediction": "Error conectando con DataMind.", "status": resp.status_code}
    except Exception as e:
        logger.exception("Error DataMind: %s", e)
        info_dm = {"prediction": "Error interno conectando a DataMind.", "detalle": str(e)}

    mensaje_final = construir_mensaje_tipster(
        consulta_usuario=texto,
        info_dm=info_dm,
        info_codigo=info_codigo,
        es_premium=es_premium,
    )

    await update.message.reply_text(mensaje_final, parse_mode="Markdown")


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# -------------------------------------------------
# RUTAS FLASK
# -------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "NumerIA Bot funcionando correctamente. 🚀", 200


@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        logger.exception("Error procesando update: %s", e)
    return "OK", 200


# -------------------------------------------------
# LOCAL (Render no lo usa)
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
