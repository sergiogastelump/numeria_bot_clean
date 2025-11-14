from collections import Counter


def reduce_to_single_digit(n: int) -> int:
    """Reduce un número a un solo dígito (1–9)."""
    if n <= 0:
        return 0
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def find_most_common_number(values: list[int]) -> int | None:
    """Devuelve el número más frecuente de la lista, o None si está vacía."""
    filtered = [v for v in values if isinstance(v, int)]
    if not filtered:
        return None
    counter = Counter(filtered)
    num, _count = counter.most_common(1)[0]
    return num
