# Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application for placing orders on the **Binance USDT-M Futures Testnet**.

> ⚠️ **Note for Indian Users**: Binance Futures Testnet (`testnet.binancefuture.com`) is geo-restricted in India. If you face a redirect, use a VPN (e.g. Proton VPN free) to access the testnet and generate API credentials. The bot code itself works without any VPN once credentials are set.

---

## Features

- ✅ MARKET, LIMIT, and STOP_MARKET orders (BUY & SELL)
- ✅ Clean CLI via `argparse` with full input validation
- ✅ Layered architecture: `client.py` → `orders.py` → `cli.py`
- ✅ Structured logging to daily log files (file + console)
- ✅ Full error handling: validation, API errors, network failures
- ✅ No third-party Binance SDK — pure REST + HMAC-SHA256 signing

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (auth, signing, HTTP)
│   ├── orders.py          # Order placement logic + response formatting
│   ├── validators.py      # Input validation helpers
│   └── logging_config.py  # File + console logging setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   └── trading_bot_YYYYMMDD.log   # Auto-created daily log file
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites
- Python 3.9+
- A free Binance Futures Testnet account

### 2. Create a Testnet Account
1. Visit 👉 [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your **GitHub account**
3. Click **API Key** in the top menu
4. Click **Generate** → copy your **API Key** and **Secret Key**

### 3. Install Dependencies
```bash
cd trading_bot
pip install -r requirements.txt
```

### 4. Set API Credentials as Environment Variables

**macOS / Linux:**
```bash
export BINANCE_API_KEY="your_testnet_api_key_here"
export BINANCE_API_SECRET="your_testnet_api_secret_here"
```

**Windows (Command Prompt):**
```cmd
set BINANCE_API_KEY=your_testnet_api_key_here
set BINANCE_API_SECRET=your_testnet_api_secret_here
```

> 🔒 Never hardcode or share your API keys anywhere.

---

## Usage

### General Syntax
```bash
python cli.py --symbol SYMBOL --side BUY|SELL --type MARKET|LIMIT|STOP_MARKET --quantity QTY [options]
```

### Place a MARKET Order
```bash
# Buy 0.001 BTC at market price
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Sell 0.01 ETH at market price
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT Order
```bash
# Sell 0.001 BTC at $115,000
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 115000

# Buy 0.001 BTC at $95,000 with GTC time-in-force
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 95000 --tif GTC
```

### Place a STOP_MARKET Order *(Bonus)*
```bash
# Stop-loss: sell if price drops to $78,000
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --price 78000
```

### All Available Flags
```
Required:
  --symbol      Trading pair, e.g. BTCUSDT
  --side        BUY or SELL
  --type        MARKET, LIMIT, or STOP_MARKET
  --quantity    Order quantity

Optional:
  --price       Limit price (LIMIT) or stop trigger price (STOP_MARKET)
  --tif         Time-in-force: GTC (default) | IOC | FOK
  --log-dir     Log directory (default: logs)
  --log-level   DEBUG | INFO | WARNING | ERROR (default: DEBUG)
```

---

## Example Output

```
┌─ ORDER REQUEST SUMMARY ──────────────────────────
│  Symbol    : BTCUSDT
│  Side      : BUY
│  Type      : MARKET
│  Quantity  : 0.001
└───────────────────────────────────────────────────

──────────────────────────────────────────────────
  ORDER PLACED SUCCESSFULLY
──────────────────────────────────────────────────
  Order ID    : 4751839201
  Symbol      : BTCUSDT
  Side        : BUY
  Type        : MARKET
  Status      : FILLED
  Orig Qty    : 0.001
  Executed Qty: 0.001
  Avg Price   : 107432.50
──────────────────────────────────────────────────

✅  Order placed successfully!
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log` (one file per day).

- **File handler**: DEBUG level — full request/response details
- **Console handler**: INFO level — key events only

### Sample Log Format
```
2025-07-10 14:02:01 | DEBUG    | trading_bot.client | → POST /fapi/v1/order  params={...}
2025-07-10 14:02:02 | DEBUG    | trading_bot.client | ← HTTP 200  body={...}
2025-07-10 14:02:02 | INFO     | trading_bot.orders | Order placed — id=4751839201  status=FILLED
```

Sample log files from testnet runs are included in the `logs/` directory.

---

## Error Handling

| Scenario | Exit Code | Behaviour |
|---|---|---|
| Invalid input (bad symbol, missing price, etc.) | 2 | Prints validation error, no API call made |
| Binance API error (e.g. insufficient margin) | 3 | Prints API error code + message |
| Network timeout | 4 | Prints timeout message |
| Connection error | 4 | Prints connection error details |

---

## Assumptions

1. **Testnet only** — Base URL is hardcoded to `https://testnet.binancefuture.com`. For mainnet, change `TESTNET_BASE_URL` in `bot/client.py`.
2. **One-way mode** — All orders use `positionSide=BOTH` (default testnet setting, no hedge mode).
3. **Precision** — The bot does not auto-enforce symbol lot size or price tick filters. If the exchange rejects an order due to precision, adjust the quantity manually (e.g. use `0.001` for BTC).
4. **Credentials via env vars** — Recommended for security. Keys are never hardcoded in source files.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `requests` | ≥ 2.31.0 | HTTP client for Binance REST API |

No third-party Binance SDK required — all API interactions use raw REST calls with HMAC-SHA256 signing.
