"""
Input validation helpers for CLI arguments.
All validators raise ValueError with a descriptive message on failure.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Ensure the symbol is a non-empty uppercase string (e.g. BTCUSDT)."""
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalnum():
        raise ValueError(
            f"Invalid symbol '{symbol}'. Must be alphanumeric (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL (case-insensitive)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Ensure order type is one of the supported types."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> float:
    """Ensure quantity is a positive number."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """
    Validate price field.
    - LIMIT and STOP_MARKET orders require a positive price.
    - MARKET orders must not provide a price (it will be ignored with a warning).
    """
    if order_type == "MARKET":
        return None  # price is irrelevant for MARKET orders

    if price is None or price == "":
        raise ValueError(
            f"A price is required for {order_type} orders."
        )
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")
    return p


def validate_stop_price(stop_price: str | float | None, order_type: str) -> float | None:
    """Stop price is required for STOP_MARKET orders."""
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None or stop_price == "":
        raise ValueError("A stop price (--stop-price) is required for STOP_MARKET orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero, got {sp}.")
    return sp
