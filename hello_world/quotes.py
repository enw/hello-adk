from decimal import Decimal, DecimalException, ROUND_HALF_UP


def calculate_quote(
    unit_price: str, quantity: int, tax_percent: str = "0", currency: str = "USD"
) -> dict:
    """Calculate a read-only USD quote, not a purchase.

    Args:
        unit_price: Nonnegative finite unit price as a decimal string.
        quantity: Positive integer number of identical items.
        tax_percent: Decimal percentage from 0 to 100, defaulting to zero.
        currency: Only USD is supported.
    """
    if currency != "USD":
        return {"error": "Only USD is supported; request a USD quote."}
    if type(quantity) is not int or quantity <= 0:
        return {"error": "Quantity must be a positive integer."}
    for name, value in (("Unit price", unit_price), ("Tax percentage", tax_percent)):
        try:
            if not isinstance(value, str):
                return {"error": f"{name} must be a finite nonnegative decimal string."}
            number = Decimal(value)
            if not number.is_finite() or number < 0:
                return {"error": f"{name} must be finite and nonnegative."}
        except DecimalException:
            return {"error": f"{name} must be a valid decimal string."}
    if Decimal(tax_percent) > 100:
        return {"error": "Tax percentage must be between 0 and 100."}
    try:
        subtotal = (Decimal(unit_price) * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = (subtotal * Decimal(tax_percent) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "subtotal": str(subtotal), "tax": str(tax),
            "total": str(subtotal + tax), "currency": currency,
        }
    except DecimalException:
        return {"error": "Quote exceeds supported decimal precision; use smaller values."}
