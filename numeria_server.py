import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler

# =========================================
# ENVIRONMENT
# =========================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL")

if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN no está configurado en Render.")

if not DATAMIND_API_URL:
    raise RuntimeError("❌ DATAMIND_API_URL no está configurado en Render.")

# =========================================
# FLASK APP
# =========================================
app = Flask(__name__)

# =========================================
# TELEGRAM APP (SYNC, ESTABLE)
# =========================================
telegram_app = ApplicationBuilder().token(TOKEN).build()


# ============================================================
# 🔮 MOTOR NUMEROLÓGICO BASE (interpretación general)
# ============================================================
def interpretar_numero(numero):
    numero = int(numero)

    significados = {
        1: "Liderazgo, impulso, inicio. En el camino deportivo indica energía que empuja hacia adelante.",
        2: "Cooperación, equilibrio. En apuestas indica análisis, prudencia y decisiones calculadas.",
        3: "Creatividad, expansión. Puede indicar partidos con goles o movimientos inesperados.",
        4: "Orden, estructura. Suelen ser marcadores cerrados o juegos más tácticos.",
        5: "Movimiento, cambio. Partidos dinámicos, goles y variaciones fuertes.",
        6: "Responsabilidad, armonía. Energía estable, balanceada, confiable.",
        7: "Intuición, análisis profundo. Buena vibración para predicciones inteligentes.",
        8: "Poder, éxito, resultados fuertes. Indica tendencias claras y marcadores contundentes.",
        9: "Cierre de ciclos, conclusiones. Buen número para últimas jornadas y definiciones."
    }

    vibraciones = {
        1: "positiva",
        2: "neutral",
        3: "positiva",
        4: "neutral",
        5: "volátil",
        6: "estable",
        7: "intuitiva",
        8: "muy positiva",
        9: "decisiva"
    }

    return significados.get(numero, "Número fuera de rango"), vibraciones.get(numero, "desconocida")


# ============================================================
# 🔮 PROCESADOR CENTRAL DE MENSAJES
# ============================================================
def procesar_interpretacion(texto):
    # Solo aceptamos números por ahora
    limpio = ''.join(c for c in texto if c.isdigit())

    if not limpio:
        return (
            "🔮 *NumerIA – Interpretación Inicial*\n"
            "Envía un *número*, una *fecha* o un *código* para obtener una interpretación."
        )

    # Reducimos numerológicamente
    n = sum(int(d) for d in limpio)
    while n > 9:
        n = sum(int(d) for d in str(n))

    significado, vibracion = interpretar_numero(n)

    return (
        f"🔢 *Número Base:* {n}\n"
        f"✨ *Vibración:* {vibracion}\n\n"
        f"📘 *Interpretación:* {significado}\n\n"
        f"🎯 *Conclusión Tipster:* Según esta vibración, "
        f"la energía actual se inclina hacia un escenario *{vibracion}*, lo que puede influir "
        f"en desempeño, marcador o tendencia del evento consultado."
    )


# ============================================================
# 🔹 HANDLERS
# ============================================================
def start(update: Update, context):
    update.message.reply_text(
        "🌟 *Bienvenido a NumerIA* 🌟\n"
        "Soy tu asistente numerológico deportivo.\n\n"
        "Envía un número, fecha o código para iniciar tu lectura."
    )

def help_cmd(update: Update, context):
    update.message.reply_text(
        "📘 *Ayuda de NumerIA*\n\n"
        "Puedes enviar:\n"
        "• Un número (ej: 27)\n"
        "• Una fecha (ej: 12/05/1998)\n"
        "• Un código místico\n\n"
        "Y obtendrás una interpretación + conclusión estilo tipster."
    )

def handle_message(update: Update, context):
    texto = update.message.text
    respuesta = procesar_interpretacion(texto)
    update.message.reply_text(respuesta, parse_mode="Markdown")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_cmd))
telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))


# ============================================================
# WEBHOOK
# ============================================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    update = Update.de_json(data, telegram_app.bot)
    telegram_app.process_update(update)
    return "ok", 200


@app.route("/")
def home():
    return "NumerIA Bot Activo 🔮", 200


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
