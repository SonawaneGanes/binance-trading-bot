#!/usr/bin/env python3
"""
cli.py — Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.001 --price 80000
  python cli.py --symbol BTCUSDT --side BUY  --type STOP_MARKET --quantity 0.001 --stop-price 78000

API credentials are read from environment variables:
  BINANCE_API_KEY
  BINANCE_API_SECRET

Or you may pass them directly via --api-key / --api-secret (not recommended for production).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from bot.client import BinanceFuturesClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import place_market_order, place_limit_order, place_stop_market_order
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = logging.getLogger("trading_bot.cli")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Credentials (optional — prefer env vars)
    creds = parser.add_argument_group("API credentials (prefer env vars)")
    creds.add_argument("--api-key", default=None, help="Binance API key (or set BINANCE_API_KEY)")
    creds.add_argument("--api-secret", default=None, help="Binance API secret (or set BINANCE_API_SECRET)")

    # Order parameters
    order = parser.add_argument_group("Order parameters")
    order.add_argument("--symbol",     required=True, help="Trading pair, e.g. BTCUSDT")
    order.add_argument("--side",       required=True, choices=["BUY", "SELL"], help="BUY or SELL")
    order.add_argument("--type",       required=True, dest="order_type",
                       choices=["MARKET", "LIMIT", "STOP_MARKET"],
                       help="Order type: MARKET, LIMIT, or STOP_MARKET")
    order.add_argument("--quantity",   required=True, type=float, help="Order quantity")
    order.add_argument("--price",      type=float, default=None, help="Limit price (required for LIMIT)")
    order.add_argument("--stop-price", type=float, default=None, dest="stop_price",
                       help="Trigger price (required for STOP_MARKET)")
    order.add_argument("--tif",        default="GTC", choices=["GTC", "IOC", "FOK"],
                       help="Time-in-force for LIMIT orders (default: GTC)")

    # Misc
    parser.add_argument("--log-dir",   default="logs", help="Directory for log files (default: logs)")
    parser.add_argument("--log-level", default="DEBUG",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Log verbosity (default: DEBUG)")

    return parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    api_key    = args.api_key    or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            "\n[ERROR] API credentials not found.\n"
            "Set environment variables:\n"
            "  export BINANCE_API_KEY='your_key'\n"
            "  export BINANCE_API_SECRET='your_secret'\n"
            "Or pass --api-key / --api-secret flags.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key, api_secret


def _print_request_summary(args: argparse.Namespace) -> None:
    print("\n" + "═" * 50)
    print("  ORDER REQUEST SUMMARY")
    print("═" * 50)
    print(f"  Symbol        : {args.symbol}")
    print(f"  Side          : {args.side}")
    print(f"  Type          : {args.order_type}")
    print(f"  Quantity      : {args.quantity}")
    if args.order_type == "LIMIT":
        print(f"  Price         : {args.price}")
        print(f"  Time-in-Force : {args.tif}")
    if args.order_type == "STOP_MARKET":
        print(f"  Stop Price    : {args.stop_price}")
    print("═" * 50 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_dir=args.log_dir, log_level=log_level)

    logger.debug("Parsed CLI arguments: %s", vars(args))

    # ── Validate inputs ──────────────────────────────────────────────────
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity   = validate_quantity(args.quantity)
        price      = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n[VALIDATION ERROR] {exc}\n", file=sys.stderr)
        sys.exit(2)

    # ── Print request summary ────────────────────────────────────────────
    args.symbol = symbol
    args.side   = side
    args.order_type = order_type
    _print_request_summary(args)

    # ── Resolve credentials & build client ───────────────────────────────
    api_key, api_secret = _resolve_credentials(args)
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)

    # ── Place order ──────────────────────────────────────────────────────
    try:
        if order_type == "MARKET":
            result = place_market_order(client, symbol, side, quantity)

        elif order_type == "LIMIT":
            result = place_limit_order(client, symbol, side, quantity, price, args.tif)

        elif order_type == "STOP_MARKET":
            result = place_stop_market_order(client, symbol, side, quantity, stop_price)

        else:
            raise ValueError(f"Unhandled order type: {order_type}")

    except BinanceClientError as exc:
        logger.error("Binance API error: code=%s msg=%s", exc.code, exc.message)
        print(f"\n[API ERROR] {exc}\n", file=sys.stderr)
        sys.exit(3)

    except Exception as exc:  # network / unexpected errors
        logger.exception("Unexpected error while placing order: %s", exc)
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        sys.exit(4)

    # ── Print result ─────────────────────────────────────────────────────
    print(result.pretty())
    logger.debug("Full order response: %s", json.dumps(result.raw, indent=2))
    print("\n✅  Order placed successfully!\n")


if __name__ == "__main__":
    main()
