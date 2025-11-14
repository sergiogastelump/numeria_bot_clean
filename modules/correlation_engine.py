from utils.helpers import find_most_common_number


def build_correlation_insights(numerology_info: dict, gematria_info: dict, sport_context: dict, dm_result: dict) -> dict:
    """
    Construye un resumen de correlaciones numéricas:
    - coincidencias entre:
      • reduced fecha
      • day_of_year_reduced
      • gematrías de equipos/jugador
    - genera un pequeño análisis lógico.
    """
    correlations = []

    date_reduced = numerology_info.get("reduced")
    day_of_year_red = numerology_info.get("day_of_year_reduced")

    # Recolectar todos los valores gemátricos
    values = []
    labels = []

    for key, data in gematria_info.items():
        for mode in ("ordinal", "full_reduction", "reverse_ordinal", "reverse_full_reduction"):
            val = data.get(mode)
            if val:
                values.append(val)
                labels.append((key, mode, val))

    # Añadimos números de fecha para buscar coincidencias
    if date_reduced:
        values.append(date_reduced)
        labels.append(("date_reduced", "reduction", date_reduced))

    if day_of_year_red:
        values.append(day_of_year_red)
        labels.append(("day_of_year_reduced", "reduction", day_of_year_red))

    # Número más común entre todos
    most_common = find_most_common_number(values)

    if most_common is not None:
        involved = [(k, m, v) for (k, m, v) in labels if v == most_common]

        correlations.append({
            "number": most_common,
            "matches": involved,
            "explanation": (
                f"El número {most_common} aparece repetido en la combinación de nombres/fecha. "
                "Cuando un mismo número se repite en equipos/jugador y fecha, se interpreta como un patrón numérico "
                "relevante que refuerza la lectura estadística."
            ),
        })

    return {
        "primary_correlations": correlations,
    }
