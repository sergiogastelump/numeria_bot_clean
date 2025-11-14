def build_header_block(user_text: str, sport_context: dict) -> str:
    """Encabezado tipo tipster profesional."""
    t1 = sport_context.get("team1_name")
    t2 = sport_context.get("team2_name")

    if t1 and t2:
        title = f"*PREDICCIÓN NUMERIA – {t1} vs {t2}*"
    else:
        title = f"*Lectura NumerIA para:* {user_text}"

    return f"🔥 {title}"


def build_datamind_block(dm_result: dict, sport_context: dict) -> str:
    """Bloque con la interpretación de DataMind."""
    prediction = dm_result.get("prediction", "Sin predicción específica.")
    confidence = dm_result.get("confidence", 0.5)
    extra = dm_result.get("extra") or {}

    lines = []
    lines.append("📊 *Análisis deportivo (DataMind)*")
    lines.append(f"• Tendencia principal: {prediction}")
    lines.append(f"• Confianza modelo: {round(confidence * 100, 1)}%")

    # Algunos campos opcionales
    avg_goals = extra.get("avg_goals_h2h")
    if avg_goals is not None:
        lines.append(f"• Goles promedio en H2H: {avg_goals:.2f}")

    winner_text = extra.get("winner_text")
    if winner_text:
        lines.append(f"• Ventaja histórica: {winner_text}")

    suggested = extra.get("suggested_markets") or []
    if suggested:
        pretty = ", ".join(suggested)
        lines.append(f"• Mercados interesantes: {pretty}")

    return "\n".join(lines)


def build_numeric_block(numerology_info: dict, gematria_info: dict) -> str:
    """Bloque de numerología técnica + gematría técnica."""
    lines = []
    lines.append("🔢 *Resumen numérico técnico*")

    date_str = numerology_info.get("date_str")
    reduced = numerology_info.get("reduced")
    day_of_year = numerology_info.get("day_of_year")
    day_of_year_red = numerology_info.get("day_of_year_reduced")
    days_left = numerology_info.get("days_left_in_year")

    if date_str:
        lines.append(f"• Fecha de análisis (UTC): {date_str}")
    if reduced is not None:
        lines.append(f"• Suma numerológica de la fecha: {numerology_info['base_sum']} → reducción: {reduced}")
    if day_of_year is not None:
        lines.append(
            f"• Día del año: {day_of_year} → reducción: {day_of_year_red} | Días restantes del año: {days_left}"
        )

    # Gematría de equipos/jugador
    if gematria_info:
        lines.append("• Gematría técnica (equipos/jugador):")
        for key, data in gematria_info.items():
            name = data.get("name", key)
            ord_ = data.get("ordinal")
            fr = data.get("full_reduction")
            rev = data.get("reverse_ordinal")
            rfr = data.get("reverse_full_reduction")

            lines.append(
                f"   - {name}: Ord={ord_}, FR={fr}, Rev={rev}, RFR={rfr}"
            )

    return "\n".join(lines)


def build_correlation_block(correlation_info: dict) -> str:
    """Bloque que explica correlaciones numéricas lógicas."""
    corrs = correlation_info.get("primary_correlations") or []
    if not corrs:
        return "📈 *Patrones numéricos:* Sin correlaciones fuertes detectadas, se prioriza principalmente el modelo estadístico."

    lines = []
    lines.append("📈 *Patrones numéricos relevantes*")

    for c in corrs:
        num = c.get("number")
        matches = c.get("matches") or []
        explanation = c.get("explanation") or ""
        labels_str = []
        for (k, mode, v) in matches:
            labels_str.append(f"{k} ({mode}={v})")
        joined = ", ".join(labels_str)
        lines.append(f"• Número destacado: {num} aparece en: {joined}")
        if explanation:
            lines.append(f"  {explanation}")

    return "\n".join(lines)


def build_pick_block(dm_result: dict, sport_context: dict) -> str:
    """Construye la parte de 'Pick NumerIA' a partir del resultado de DataMind y contexto."""
    prediction = dm_result.get("prediction", "Lectura general.")
    confidence = dm_result.get("confidence", 0.5)
    extra = dm_result.get("extra") or {}

    suggested = extra.get("suggested_markets") or []
    if suggested:
        main_pick = suggested[0]
    else:
        main_pick = prediction

    t1 = sport_context.get("team1_name")
    t2 = sport_context.get("team2_name")

    if t1 and t2:
        title = f"{t1} vs {t2}"
    else:
        title = sport_context.get("raw_text") or "Evento"

    lines = []
    lines.append("🔥 *Pick NumerIA*")
    lines.append(f"• Partido / Evento: {title}")
    lines.append(f"• Recomendación principal: *{main_pick}*")
    lines.append(f"• Basado en: tendencia estadística + patrones numéricos técnicos.")
    lines.append(f"• Nivel de confianza NumerIA: {round(confidence * 100, 1)}%")

    return "\n".join(lines)
