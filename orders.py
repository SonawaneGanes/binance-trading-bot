"""
Order placement logic — high-level wrappers over BinanceFuturesClient.
Each function constructs the correct parameter set, calls the client,
and returns a normalised OrderResult dataclass.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from bot.client import BinanceFuturesClient

logger = logging.getLogger("trading_bot.orders")


@dataclass
class OrderResult:
    """Normalised representation of a Binance order response."""

    order_id: int
    symbol: str
    side: str
    order_type: str
    status: str
    orig_qty: str
    executed_qty: str
    avg_price: str
    price: str
    stop_price: str
    time_in_force: str
    raw: Dict[str, Any] = field(repr=False)

    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "OrderResult":
        return cls(
            order_id=data.get("orderId", 0),
            symbol=data.get("symbol", ""),
            side=data.get("side", ""),
            order_type=data.get("type", ""),
            status=data.get("status", ""),
            orig_qty=data.get("origQty", "0"),
            executed_qty=data.get("executedQty", "0"),
            avg_price=data.get("avgPrice", "0"),
            price=data.get("price", "0"),
            stop_price=data.get("stopPrice", "0"),
            time_in_force=data.get("timeInForce", ""),
            raw=data,
        )

    def pretty(self) -> str:
        """Return a human-readable summary of the order result."""
        lines = [
            "─" * 50,
            "  ORDER RESULT",
            "─" * 50,
            f"  Order ID      : {self.order_id}",
            f"  Symbol        : {self.symbol}",
            f"  Side          : {self.side}",
            f"  Type          : {self.order_type}",
            f"  Status        : {self.status}",
            f"  Orig Qty      : {self.orig_qty}",
            f"  Executed Qty  : {self.executed_qty}",
            f"  Avg Price     : {self.avg_price}",
        ]
        if self.order_type == "LIMIT":
            lines.append(f"  Limit Price   : {self.price}")
            lines.append(f"  Time In Force : {self.time_in_force}")
        if self.order_type == "STOP_MARKET":
            lines.append(f"  Stop Price    : {self.stop_price}")
        lines.append("─" * 50)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Order placement helpers
# ---------------------------------------------------------------------------

def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
) -> OrderResult:
    """
    Place a MARKET order.

    Args:
        client: Authenticated BinanceFuturesClient.
        symbol: Trading pair (e.g. 'BTCUSDT').
        side: 'BUY' or 'SELL'.
        quantity: Order quantity.

    Returns:
        OrderResult dataclass.
    """
    logger.info("Placing MARKET order | %s %s qty=%s", side, symbol, quantity)
    response = client.place_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )
    return OrderResult.from_response(response)


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> OrderResult:
    """
    Place a LIMIT order.

    Args:
        client: Authenticated BinanceFuturesClient.
        symbol: Trading pair.
        side: 'BUY' or 'SELL'.
        quantity: Order quantity.
        price: Limit price.
        time_in_force: 'GTC' (default), 'IOC', or 'FOK'.

    Returns:
        OrderResult dataclass.
    """
    logger.info(
        "Placing LIMIT order | %s %s qty=%s price=%s tif=%s",
        side, symbol, quantity, price, time_in_force,
    )
    response = client.place_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=price,
        timeInForce=time_in_force,
    )
    return OrderResult.from_response(response)


def place_stop_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    stop_price: float,
) -> OrderResult:
    """
    Place a STOP_MARKET order (bonus order type).

    Args:
        client: Authenticated BinanceFuturesClient.
        symbol: Trading pair.
        side: 'BUY' or 'SELL'.
        quantity: Order quantity.
        stop_price: Trigger price.

    Returns:
        OrderResult dataclass.
    """
    logger.info(
        "Placing STOP_MARKET order | %s %s qty=%s stopPrice=%s",
        side, symbol, quantity, stop_price,
    )
    response = client.place_order(
        symbol=symbol,
        side=side,
        type="STOP_MARKET",
        quantity=quantity,
        stopPrice=stop_price,
    )
    return OrderResult.from_response(response)
