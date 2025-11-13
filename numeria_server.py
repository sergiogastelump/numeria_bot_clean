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
# 🔮 MOTOR NUMEROLÓGICO BASE
# ============================================================
def interpretar_numero(numero):
    numero = int(numero)

    significados = {
        1: "Liderazgo, impulso, inicio.",
        2: "Cooperación, equilibrio.",
        3: "Creatividad, expansión.",
        4: "Orden, estructura.",
        5: "Movimiento, cambio.",
        6: "Responsabilidad, armonía.",
        7: "Intuición, análisis profundo.",
        8: "Poder, éxito, fuerza.",
        9: "Cierre de ciclos, culminación."
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
# 🔮 INTERPRETACIÓN DE CÓDIGOS MÍSTICOS (nuevo)
# ============================================================
CODIGOS_MISTICOS = {
    "111": "Portal de intención. Inicio de una nueva dirección.",
    "222": "Alineación y equilibrio. Momento de tomar decisiones meditadas.",
    "333": "Expansión y creatividad divina.",
    "444": "Protección espiritual y fortaleza interna.",
    "555": "Cambio brusco o giro inesperado.",
    "666": "Responsabilidad, enfoque interno y reflexión.",
    "777": "Intuición elevada y claridad espiritual.",
    "888": "Abundancia, éxito y avance.",
    "999": "Cierre de ciclo y concreción.",
    "1010": "Camino correcto. Avance alineado.",
    "1111": "Máximo potencial. Portal mayor de manifestación.",
    "2222": "Balance profundo. Atención a señales.",
    "4444": "Máxima protección. Buen momento para decisiones difíciles.",
    "7777": "Intuición extrema. Señales claras."
}

def procesar_codigo_mistico(texto):
    limpio = texto.replace(" ", "")
    if limpio in CODIGOS_MISTICOS:
        significado = CODIGOS_MISTICOS[limpio]

        return (
            f"✨ *Código Místico Detectado: {limpio}*\n\n"
            f"📘 *Significado:* {significado}\n\n"
            f"🎯 *Conclusión Tipster:* Este código indica una energía específica "
            f"alineada con *{significado.lower()}*. Puede influir en tendencias, "
            f"momentos clave del partido o decisiones estratégicas."
        )

    return None


# ============================================================
# 🔮 INTERPRETACIÓN DE FECHAS
# ============================================================
def procesar_fecha(texto):
    import re
    patron = r"(\d{1,2})[\/\-\s](\d{1,2})[\/\-\s](\d{2,4})"
    match = re.search(patron, texto)

    if not match:
        return None

    dia = int(match.group(1))
    mes = int(match.group(2))
    anio = int(match.group(3))

    rd = reducir(dia)
    rm = reducir(mes)
    ra = reducir(anio)
    total = reducir(rd + rm + ra)

    significado, vibracion = interpretar_numero(total)

    return (
        f"📅 *Interpretación de Fecha*\n"
        f"➡ Día: {dia} → {rd}\n"
        f"➡ Mes: {mes} → {rm}\n"
        f"➡ Año: {anio} → {ra}\n\n"
        f"🔢 *Número Final:* {total}\n"
        f"✨ *Vibración:* {vibracion}\n\n"
        f"📘 *Significado:* {significado}\n\n"
        f"🎯 *Conclusión Tipster:* Esta fecha tiene una energía *{vibracion}*, "
        f"indicando escenarios alineados con esa vibración."
    )


# ============================================================
# 🔹 REDUCCIÓN NUMEROLÓGICA
# ============================================================
def reducir(n):
    n = int(n)
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


# ============================================================
# 🔮 PROCESADOR CENTRAL
# ============================================================
def procesar_interpretacion(texto):
    # 1) Códigos místicos
    cod = procesar_codigo_mistico(texto)
    if cod:
        return cod

    # 2) Fechas
    respuesta_fecha = procesar_fecha(texto)
    if respuesta_fecha:
        return respuesta_fecha

    # 3) Números normales
    limpio = ''.join(c for c in texto if c.isdigit())
    if not limpio:
        return (
            "🔮 *NumerIA – Guía rápida*\n"
            "Puedes enviar:\n"
            "• Un número (27)\n"
            "• Una fecha (12/05/1998)\n"
            "• Un código místico (111, 4444, 777)\n"
        )

    n = reducir(limpio)
    significado, vibracion = interpretar_numero(n)

    return (
        f"🔢 *Número Base:* {n}\n"
        f"✨ *Vibración:* {vibracion}\n\n"
        f"📘 *Interpretación:* {significado}\n\n"
        f"🎯 *Conclusión Tipster:* Escenario con energía *{vibracion}*."
    )


# ============================================================
# HANDLERS
# ============================================================
def start(update: Update, context):
    update.message.reply_text(
        "🌟 *Bienvenido a NumerIA* 🌟\n"
        "Soy tu asistente numerológico deportivo.\n\n"
        "Envía un número, una fecha o un código místico.",
        parse_mode="Markdown"
    )

def help_cmd(update: Update, context):
    update.message.reply_text(
        "📘 *Ayuda de NumerIA*\n\n"
        "Puedes enviar:\n"
        "• Un número (27)\n"
        "• Una fecha (12/05/1998)\n"
        "• Un código místico (111, 7777, 444)\n",
        parse_mode="Markdown"
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
