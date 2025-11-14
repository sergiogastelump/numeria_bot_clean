from datetime import datetime


def _reduce_to_single_digit(n: int) -> int:
    """Reduce un número a 1 dígito (1–9) usando suma de dígitos."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def get_date_numerology(dt: datetime | None = None) -> dict:
    """
    Calcula numerología técnica de la fecha:
    - fecha en texto
    - suma básica
    - reducción 1–9
    - día del año
    - reducción del día del año
    - días restantes del año
    """
    if dt is None:
        dt = datetime.utcnow()

    year = dt.year
    month = dt.month
    day = dt.day

    base_sum = year + month + day
    reduced = _reduce_to_single_digit(base_sum)

    day_of_year = int(dt.strftime("%j"))  # 1..365
    day_of_year_reduced = _reduce_to_single_digit(day_of_year)

    # No nos complicamos con años bisiestos aquí
    days_in_year = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
    days_left = days_in_year - day_of_year

    return {
        "date_str": dt.strftime("%Y-%m-%d"),
        "year": year,
        "month": month,
        "day": day,
        "base_sum": base_sum,
        "reduced": reduced,
        "day_of_year": day_of_year,
        "day_of_year_reduced": day_of_year_reduced,
        "days_left_in_year": days_left,
    }
