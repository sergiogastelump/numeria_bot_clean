import os
import json
import urllib.request
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, MessageHandler, Filters

# ================================
# VARIABLES DE ENTORNO
# ================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
DATAMIND_API_URL = os.getenv("DATAMIND_API_URL")

if not TOKEN:
    raise RuntimeError("FALTA TELEGRAM_TOKEN en las Environment Variables.")

if not DATAMIND_API_URL:
    raise RuntimeError("FALTA DATAMIND_API_URL en las Environment Variables.")

# ================================
# FLASK
# ================================
app = Flask(__name__)

# ================================
# TELEGRAM (SÍNCRONO)
# ================================
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# ================================
# FUNCIÓN: Interpretación Numerológica
# ================================
def interpretar_numerologia(texto):
    total = sum(ord(c) for c in texto)
    numero = total % 9 or 9

    interpretaciones = {
        1: "Nuevo comienzo energético. Tendencia ofensiva.",
        2: "Energía equilibrada. Posibilidad alta de empate.",
        3: "Vibración creativa. Partido con goles.",
        4: "Control táctico. Partido cerrado.",
        5: "Energía cambiante. Resultado inesperado.",
        6: "Armonía. Buen rendimiento del local.",
        7: "Análisis profundo. Juego estratégico.",
        8: "Poder y dominio físico.",
        9: "Cierre de ciclo. Marcador amplio probable."
    }

    return numero, interpretaciones[numero]

# ================================
# FUNCIÓN: Consultar DataMind (POST)
# ================================
def consultar_datamind(consulta_texto):
    payload = json.dumps({"consulta": consulta_texto}).encode("utf-8")

    try:
        req = urllib.request.Request(
            DATAMIND_API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        return data

    except Exception as e:
        return {"error": str(e)}

# ================================
# HANDLER DE MENSAJES
# ================================
def handle_message(update, context):
    texto = update.message.text

    # 1) Interpretación numerológica
    numero, significado = interpretar_numerologia(texto)

    # 2) Llamada a DataMind
    resultado_ia = consultar_datamind(texto)

    if "error" in resultado_ia:
        respuesta = (
            f"🔮 *NumerIA – Interpretación Mística*\n"
            f"Número maestro: *{numero}*\n"
            f"Significado: _{significado}_\n\n"
            f"⚠️ DataMind no respondió.\n"
            f"Tipster solo con numerología."
        )
    else:
        pred = resultado_ia["prediccion"]
        confi = resultado_ia["confianza"]
        analisis = resultado_ia.get("analisis", "Sin análisis adicional.")

        respuesta = (
            f"🔮 *NumerIA – Modo Tipster Híbrido*\n\n"
            f"📌 *Consulta:* {texto}\n\n"
            f"✨ *Numerología*\n"
            f"Número maestro: *{numero}*\n"
            f"Interpretación: _{significado}_\n\n"
            f"🤖 *IA DataMind*\n"
            f"- Local: {pred['local']}%\n"
            f"- Empate: {pred['empate']}%\n"
            f"- Visita: {pred['visita']}%\n"
            f"- Confianza del modelo: {int(confi*100)}%\n"
            f"Análisis IA: _{analisis}_\n\n"
            f"🎯 *Conclusión Tipster*\n"
            f"Combinando numerología + IA, la inclinación final es: *{max(pred, key=pred.get).upper()}*."
        )

    update.message.reply_text(respuesta, parse_mode="Markdown")

# Registrar handler
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# ================================
# WEBHOOK
# ================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    dispatcher.process_update(update)
    return "ok", 200

@app.route("/")
def index():
    return "NumerIA bot activo ✔", 200

# ================================
# RUN
# ================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
