import string
from utils.helpers import reduce_to_single_digit


def _build_alpha_maps():
    letters = string.ascii_lowercase  # a..z
    ordinal = {ch: i + 1 for i, ch in enumerate(letters)}              # a=1..z=26
    reverse = {ch: 26 - i for i, ch in enumerate(letters)}             # a=26..z=1
    return ordinal, reverse


ORDINAL_MAP, REVERSE_MAP = _build_alpha_maps()


def _normalize_text(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalpha())


def gematria_ordinal(text: str) -> int:
    t = _normalize_text(text)
    return sum(ORDINAL_MAP.get(ch, 0) for ch in t)


def gematria_full_reduction(text: str) -> int:
    return reduce_to_single_digit(gematria_ordinal(text))


def gematria_reverse_ordinal(text: str) -> int:
    t = _normalize_text(text)
    return sum(REVERSE_MAP.get(ch, 0) for ch in t)


def gematria_reverse_full_reduction(text: str) -> int:
    return reduce_to_single_digit(gematria_reverse_ordinal(text))


def get_gematria_summary(sport_context: dict) -> dict:
    """
    Calcula gematría de los elementos clave:
    - team1_name
    - team2_name
    - main_player (si existe)
    Devuelve un dict con los 4 sistemas.
    """
    names = []
    if sport_context.get("team1_name"):
        names.append(("team1", sport_context["team1_name"]))
    if sport_context.get("team2_name"):
        names.append(("team2", sport_context["team2_name"]))
    if sport_context.get("main_player"):
        names.append(("player", sport_context["main_player"]))

    summary = {}
    for key, value in names:
        summary[key] = {
            "name": value,
            "ordinal": gematria_ordinal(value),
            "full_reduction": gematria_full_reduction(value),
            "reverse_ordinal": gematria_reverse_ordinal(value),
            "reverse_full_reduction": gematria_reverse_full_reduction(value),
        }

    return summary
