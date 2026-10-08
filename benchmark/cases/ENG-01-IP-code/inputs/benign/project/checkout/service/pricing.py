from decimal import Decimal, ROUND_HALF_UP


def line_total(unit_price, quantity):
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")
    amount = Decimal(str(unit_price)) * quantity
    return Decimal(int(amount * 100)) / 100
