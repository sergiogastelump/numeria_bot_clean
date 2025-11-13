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

    return significados[numero], vibraciones[numero]


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

        return {
            "codigo": limpio,
            "significado": significado,
            "vibracion": "mística",
            "texto": (
                f"✨ *Código Místico Detectado: {limpio}*\n\n"
                f"📘 *Significado:* {significado}\n\n"
                f"🎯 *Conclusión Tipster:* Energía espiritual activa que puede marcar "
                f"momentos clave o influir en decisiones deportivas."
            )
        }

    return None


# ============================================================
# 🔮 NOMBRES → NÚMERO
# ============================================================
def nombre_a_numero(nombre):
    nombre = nombre.replace(" ", "").upper()
    if not nombre.isalpha():
        return None

    return sum(ord(c) - 64 for c in nombre)

def procesar_nombre(texto):
    total = nombre_a_numero(texto)
    if not total:
        return None

    reducido = reducir(total)
    significado, vibracion = interpretar_numero(reducido)

    return {
        "nombre": texto,
        "total": total,
        "reducido": reducido,
        "significado": significado,
        "vibracion": vibracion,
        "texto": (
            f"🔤 *Interpretación de Nombre*\n"
            f"➡ Valor total: {total}\n"
            f"➡ Reducción: {reducido}\n\n"
            f"📘 *Significado:* {significado}\n"
            f"✨ *Vibración:* {vibracion}\n"
        )
    }


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

    return {
        "dia": rd,
        "mes": rm,
        "anio": ra,
        "final": total,
        "significado": significado,
        "vibracion": vibracion,
        "texto": (
            f"📅 *Interpretación de Fecha*\n"
            f"➡ Día: {dia} → {rd}\n"
            f"➡ Mes: {mes} → {rm}\n"
            f"➡ Año: {anio} → {ra}\n\n"
            f"🔢 *Número Final:* {total}\n"
            f"✨ *Vibración:* {vibracion}\n"
        )
    }


# ============================================================
# 🔹 REDUCCIÓN
# ============================================================
def reducir(n):
    n = int(n)
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


# ============================================================
# 🔮 INTERPRETACIÓN CRUZADA (NOMBRE + FECHA + NÚMERO + CÓDIGO)
# ============================================================
def interpretacion_cruzada(partes):
    textos = []
    vibraciones = []

    # NOMBRE
    if partes.get("nombre"):
        textos.append(partes["nombre"]["texto"])
        vibraciones.append(partes["nombre"]["vibracion"])

    # FECHA
    if partes.get("fecha"):
        textos.append(partes["fecha"]["texto"])
        vibraciones.append(partes["fecha"]["vibracion"])

    # CÓDIGO
    if partes.get("codigo"):
        textos.append(partes["codigo"]["texto"])
        vibraciones.append("mística")

    # NÚMERO
    if partes.get("numero"):
        textos.append(partes["numero"]["texto"])
        vibraciones.append(partes["numero"]["vibracion"])

    # Vibración final
    vibracion_final = "mixta"

    if all(v in ["muy positiva", "positiva"] for v in vibraciones):
        vibracion_final = "muy positiva"
    elif all(v in ["neutral", "estable"] for v in vibraciones):
        vibracion_final = "estable"
    elif any(v == "volátil" for v in vibraciones):
        vibracion_final = "volátil"
    elif any(v == "mística" for v in vibraciones):
        vibracion_final = "mística"

    conclusion = (
        f"\n\n🎯 *Conclusión Tipster – Interpretación Cruzada*\n"
        f"La energía combinada genera una vibración *{vibracion_final}*. "
        f"Esto puede influir en tendencia, rendimiento, intensidad del juego o momentos clave.\n"
        f"Recomendación: tomar decisiones en alineación con esta vibración."
    )

    return "\n\n".join(textos) + conclusion


# ============================================================
# 🔮 PROCESADOR CENTRAL
# ============================================================
def procesar_interpretacion(texto):
    partes = {}

    # 1) Código
    cod = procesar_codigo_mistico(texto)
    if cod:
        partes["codigo"] = cod

    # 2) Fecha
    fecha = procesar_fecha(texto)
    if fecha:
        partes["fecha"] = fecha

    # 3) Nombre
    nombre = procesar_nombre(texto)
    if nombre:
        partes["nombre"] = nombre

    # 4) Número libre
    limpio = ''.join(c for c in texto if c.isdigit())
    if limpio:
        base = reducir(limpio)
        significado, vibracion = interpretar_numero(base)
        partes["numero"] = {
            "valor": base,
            "significado": significado,
            "vibracion": vibracion,
            "texto": (
                f"🔢 *Número Base Detectado:* {base}\n"
                f"📘 *Interpretación:* {significado}\n"
                f"✨ *Vibración:* {vibracion}\n"
            )
        }

    # Si solo hubo una categoría → devolver normal
    if len(partes) == 1:
        return list(partes.values())[0]["texto"]

    # Si hubo varias → interpretación cruzada profesional
    return interpretacion_cruzada(partes)


# ============================================================
# HANDLERS
# ============================================================
def start(update: Update, context):
    update.message.reply_text(
        "🌟 *Bienvenido a NumerIA* 🌟\n"
        "Interpretación numerológica místico–deportiva.\n"
        "Envía un nombre, fecha, número o código místico.\n"
        "También puedes combinarlos: 'Real Madrid 14/02/2025'.",
        parse_mode="Markdown"
    )

def help_cmd(update: Update, context):
    update.message.reply_text(
        "📘 *Ayuda*\n"
        "Ejemplos:\n"
        "• Real Madrid\n"
        "• 12/05/1998\n"
        "• 777\n"
        "• Messi 14/06/1987\n",
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
