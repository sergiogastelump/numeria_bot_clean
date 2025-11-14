import os
import logging
import requests

from modules.numerology_engine import get_date_numerology
from modules.gematria_engine import get_gematria_summary
from modules.correlation_engine import build_correlation_insights
from modules.formatter_engine import format_full_response
from utils.sports_extractors import detect_sport_and_entities

logger = logging.getLogger(__name__)

DATAMIND_URL = os.getenv("DATAMIND_URL")


def call_datamind(text: str) -> dict:
    """Llama al backend DataMind (/predict)."""
    if not DATAMIND_URL:
        logger.warning("DATAMIND_URL no configurada, usando fallback.")
        return {
            "prediction": f"Base para: {text}",
            "confidence": 0.5,
            "market": "general",
            "extra": {"note": "DATAMIND_URL no configurada."},
        }

    try:
        resp = requests.post(
            DATAMIND_URL,
            json={"input": text},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error("DataMind status != 200: %s", resp.status_code)
            return {
                "prediction": f"Base para: {text}",
                "confidence": 0.5,
                "market": "general",
                "extra": {"note": f"Error HTTP DataMind: {resp.status_code}"},
            }
        data = resp.json()
        if not isinstance(data, dict):
            logger.error("Respuesta DataMind no es dict: %s", data)
            return {
                "prediction": f"Base para: {text}",
                "confidence": 0.5,
                "market": "general",
                "extra": {"note": "Formato respuesta DataMind inválido."},
            }
        return data
    except Exception as e:
        logger.exception("Error llamando a DataMind: %s", e)
        return {
            "prediction": f"Base para: {text}",
            "confidence": 0.5,
            "market": "general",
            "extra": {"note": f"Excepción DataMind: {e}"},
        }


def generate_numeria_response(user_text: str) -> str:
    """
    Orquesta todo el flujo:
    - Llama a DataMind
    - Detecta deporte/entidades
    - Genera numerología + gematría
    - Construye correlaciones
    - Formatea en estilo tipster profesional
    """
    # 1) Llamar a DataMind
    dm_result = call_datamind(user_text)

    # 2) Detectar deporte, equipos, jugadores, etc.
    sport_context = detect_sport_and_entities(user_text, dm_result)

    # 3) Numerología técnica de la fecha (usamos fecha actual por ahora)
    numerology_info = get_date_numerology()

    # 4) Gematría técnica (nombres clave: equipos, jugador principal, etc.)
    gematria_info = get_gematria_summary(sport_context)

    # 5) Correlaciones numéricas (coincidencias lógicas, no místicas)
    correlation_info = build_correlation_insights(numerology_info, gematria_info, sport_context, dm_result)

    # 6) Formatear todo en un mensaje final
    final_text = format_full_response(
        user_text=user_text,
        sport_context=sport_context,
        numerology_info=numerology_info,
        gematria_info=gematria_info,
        correlation_info=correlation_info,
        datamind_result=dm_result,
    )

    return final_text
