def calculate_discount(price: float, percentage: float) -> float:
    """Return the price after applying a percentage discount."""
    return price * (1 - percentage / 100)
