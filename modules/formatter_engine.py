from utils.text_templates import (
    build_header_block,
    build_datamind_block,
    build_numeric_block,
    build_correlation_block,
    build_pick_block,
)


def format_full_response(
    user_text: str,
    sport_context: dict,
    numerology_info: dict,
    gematria_info: dict,
    correlation_info: dict,
    datamind_result: dict,
) -> str:
    """
    Combina TODOS los bloques en un solo texto final listo para enviar por Telegram.
    Estilo: numérico, lógico, convincente, profesional (sin misticismo raro).
    """
    blocks = []

    # 1) Encabezado
    blocks.append(build_header_block(user_text, sport_context))

    # 2) Bloque DataMind (stats / tendencia)
    blocks.append(build_datamind_block(datamind_result, sport_context))

    # 3) Bloque numérico (fecha + gematría resumida)
    blocks.append(build_numeric_block(numerology_info, gematria_info))

    # 4) Bloque correlaciones
    blocks.append(build_correlation_block(correlation_info))

    # 5) Pick final
    blocks.append(build_pick_block(datamind_result, sport_context))

    # 6) Aviso final
    blocks.append(
        "⚠️ *Aviso:* NumerIA utiliza datos reales, estadística avanzada y análisis numérico, "
        "pero ningún modelo puede garantizar resultados. Usa esta información como guía inteligente."
    )

    # Unir todo con líneas en blanco
    return "\n\n".join(block for block in blocks if block)
