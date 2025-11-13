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
# 🔮 INTERPRETACIÓN DE CÓDIGOS MÍSTICOS
# ============================================================
CODIGOS_MISTICOS = {
    "111": "Portal de intención.",
    "222": "Alineación y equilibrio.",
    "333": "Expansión y creatividad divina.",
    "444": "Protección espiritual.",
    "555": "Cambios importantes.",
    "666": "Reflexión y responsabilidad.",
    "777": "Intuición elevada.",
    "888": "Éxito y avance.",
    "999": "Cierre de ciclo.",
    "1010": "Dirección correcta.",
    "1111": "Máximo potencial.",
    "2222": "Balance profundo.",
    "4444": "Máxima protección.",
    "7777": "Intuición extrema."
}

def procesar_codigo_mistico(texto):
    limpio = texto.replace(" ", "")
    if limpio in CODIGOS_MISTICOS:
        significado = CODIGOS_MISTICOS[limpio]

        return (
            f"✨ *Código Místico Detectado: {limpio}*\n\n"
            f"📘 *Significado:* {significado}\n\n"
            f"🎯 *Conclusión Tipster:* Energía alineada con *{significado.lower()}*. "
            f"Puede influir en momentos clave o decisiones deportivas."
        )


# ============================================================
# 🔮 NOMBRES → NÚMERO
# ============================================================
def nombre_a_numero(nombre):
    nombre = nombre.replace(" ", "").upper()

    if not nombre.isalpha():
        return None

    total = sum(ord(c) - 64 for c in nombre)  # A=1, B=2...
    return total

def procesar_nombre(texto):
    total = nombre_a_numero(texto)
    if not total:
        return None

    reducido = reducir(total)
    significado, vibracion = interpretar_numero(reducido)

    return (
        f"🔤 *Interpretación de Nombre*\n"
        f"➡ Valor total: {total}\n"
        f"➡ Reducción: {reducido}\n\n"
        f"📘 *Significado:* {significado}\n"
        f"✨ *Vibración:* {vibracion}\n\n"
        f"🎯 *Conclusión Tipster:* El nombre tiene energía *{vibracion}*. "
        f"Esto puede influir en comportamiento, momentos clave o desempeño deportivo."
    )


# ============================================================
# 🔮 FECHAS
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
        f"🎯 *Conclusión Tipster:* Fecha con energía *{vibracion}*. "
        f"Influye en resultados, rendimiento o momentos clave."
    )


# ============================================================
# 🔹 REDUCCIÓN
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
    fecha = procesar_fecha(texto)
    if fecha:
        return fecha

    # 3) Nombres
    nombre = procesar_nombre(texto)
    if nombre:
        return nombre

    # 4) Números generales
    limpio = ''.join(c for c in texto if c.isdigit())
    if limpio:
        n = reducir(limpio)
        significado, vibracion = interpretar_numero(n)

        return (
            f"🔢 *Número Base:* {n}\n"
            f"✨ *Vibración:* {vibracion}\n\n"
            f"📘 *Interpretación:* {significado}\n\n"
            f"🎯 *Conclusión Tipster:* Escenario con energía *{vibracion}*."
        )

    # 5) Fallback
    return (
        "🔮 *NumerIA – Guía rápida*\n"
        "Puedes enviar:\n"
        "• Un nombre (Messi, Real Madrid)\n"
        "• Una fecha (12/05/1998)\n"
        "• Un número (27)\n"
        "• Un código místico (111, 777, 4444)\n"
    )


# ============================================================
# HANDLERS
# ============================================================
def start(update: Update, context):
    update.message.reply_text(
        "🌟 *Bienvenido a NumerIA* 🌟\n"
        "Interpretación numerológica aplicada al deporte.\n"
        "Envía un nombre, una fecha, un número o un código.",
        parse_mode="Markdown"
    )

def help_cmd(update: Update, context):
    update.message.reply_text(
        "📘 *Ayuda*\n"
        "Puedes enviar nombres, fechas, números o códigos místicos.\n",
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
