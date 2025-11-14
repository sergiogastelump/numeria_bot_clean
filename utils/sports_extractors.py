import re


def detect_sport_and_entities(user_text: str, dm_result: dict) -> dict:
    """
    Detecta deporte, equipos, jugador principal, etc.
    Por ahora:
    - Si hay 'vs' asumimos formato Equipo1 vs Equipo2
    - Deporte por defecto: 'football' si DataMind lo devuelve, si no 'unknown'
    """
    text = user_text.strip()
    lowered = text.lower()
    sport = "unknown"

    extra = dm_result.get("extra") or {}
    if isinstance(extra, dict):
        sport = extra.get("sport", sport)

    team1_name = None
    team2_name = None

    if " vs " in lowered or " vs. " in lowered or " vs" in lowered:
        # dividir por 'vs'
        parts = re.split(r"\bvs\.?\b", text, flags=re.IGNORECASE)
        if len(parts) >= 2:
            team1_name = parts[0].strip()
            team2_name = parts[1].strip()

    # Jugador principal: por ahora vacío (luego se puede alimentar desde DataMind)
    main_player = None

    return {
        "sport": sport,
        "team1_name": team1_name,
        "team2_name": team2_name,
        "main_player": main_player,
        "raw_text": user_text,
    }
