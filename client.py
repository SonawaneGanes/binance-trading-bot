"""
Low-level Binance Futures Testnet REST client.
Handles request signing, HTTP execution, and raw response parsing.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance USDT-M Futures REST API (Testnet).

    Attributes:
        api_key: Binance Futures Testnet API key.
        api_secret: Binance Futures Testnet API secret.
        base_url: Base URL for the testnet (default: TESTNET_BASE_URL).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceFuturesClient created. Base URL: %s", self.base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append a HMAC-SHA256 signature to the parameter dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request and return the parsed JSON body.

        Args:
            method: HTTP verb ('GET', 'POST', etc.).
            endpoint: API path (e.g. '/fapi/v1/order').
            params: Query / body parameters.
            signed: Whether to add a timestamp + HMAC signature.

        Returns:
            Parsed JSON response dict.

        Raises:
            BinanceClientError: On API-level error response.
            requests.RequestException: On network failures.
        """
        params = params or {}
        if signed:
            params["timestamp"] = self._timestamp()
            params = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.debug("→ %s %s | params: %s", method.upper(), url, params)

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=self.timeout)
            else:
                response = self._session.request(
                    method.upper(), url, data=params, timeout=self.timeout
                )
        except requests.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.Timeout as exc:
            logger.error("Request timed out after %ss: %s", self.timeout, exc)
            raise

        logger.debug("← HTTP %s | body: %s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response received: %s", response.text[:200])
            response.raise_for_status()
            raise

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            # Binance error envelope: {"code": -XXXX, "msg": "..."}
            raise BinanceClientError(code=data["code"], message=data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange metadata (symbols, filters, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> Dict[str, Any]:
        """Fetch account information (balances, positions)."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Place a new order on Binance Futures Testnet.

        Keyword Args:
            symbol (str): Trading pair, e.g. 'BTCUSDT'.
            side (str): 'BUY' or 'SELL'.
            type (str): 'MARKET', 'LIMIT', or 'STOP_MARKET'.
            quantity (float): Order quantity.
            price (float, optional): Required for LIMIT orders.
            stopPrice (float, optional): Required for STOP_MARKET orders.
            timeInForce (str, optional): 'GTC', 'IOC', 'FOK' (required for LIMIT).

        Returns:
            Raw order response dict from Binance.
        """
        logger.info(
            "Placing order | symbol=%s side=%s type=%s qty=%s price=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        response = self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)
        logger.info("Order placed successfully | orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return response
