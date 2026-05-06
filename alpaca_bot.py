"""
Alpaca RSI Bot — paper trading
Stratégia: kúp keď RSI < 35, predaj keď RSI > 65
Spúšťa sa raz denne (cron na VPS)
"""

import os
import datetime as dt
import requests
import yfinance as yf
import numpy as np
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ── CONFIG ────────────────────────────────────────────────────────────────────

API_KEY  = os.getenv("ALPACA_API_KEY", "PKXBR37EUJIDZ6TEDR57272UZ3")
SECRET   = os.getenv("ALPACA_SECRET",  "EomZsLEN3KXWTVxeGPFggq8Wj8fLNjcZJ9FQXrXvqAsN")

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SYMBOLS   = ["AAPL", "MSFT", "GOOGL"]
RSI_BUY   = 35
RSI_SELL  = 65
RISK_PCT  = 0.05   # 5% kapitálu na jeden obchod

# ── TELEGRAM ──────────────────────────────────────────────────────────────────

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"[WARN] Telegram: {e}")

# ── RSI ───────────────────────────────────────────────────────────────────────

def get_rsi(symbol, period=14):
    df = yf.download(symbol, period="60d", auto_adjust=True, progress=False)
    df.columns = df.columns.get_level_values(0)
    close = df["Close"].squeeze()
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean().replace(0, float("nan"))
    rsi   = 100 - 100 / (1 + gain / loss)
    return float(rsi.iloc[-1]), float(close.iloc[-1])

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    now = dt.datetime.now(dt.timezone.utc)
    print(f"[{now:%Y-%m-%d %H:%M} UTC] Alpaca RSI Bot")

    client  = TradingClient(API_KEY, SECRET, paper=True)
    account = client.get_account()
    equity  = float(account.equity)
    print(f"Equity: ${equity:,.2f}")

    # Aktuálne pozície
    positions = {p.symbol: float(p.qty) for p in client.get_all_positions()}

    for symbol in SYMBOLS:
        try:
            rsi, price = get_rsi(symbol)
            print(f"{symbol}: RSI={rsi:.1f} | Price=${price:.2f}")

            in_position = symbol in positions and positions[symbol] > 0

            if rsi < RSI_BUY and not in_position:
                # Kúp
                qty = max(1, int((equity * RISK_PCT) / price))
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
                client.submit_order(order)
                msg = f"🟢 ALPACA BUY — {symbol}\nRSI: {rsi:.1f}\nPrice: ${price:.2f}\nQty: {qty}"
                print(msg)
                send_telegram(msg)

            elif rsi > RSI_SELL and in_position:
                # Predaj
                qty = int(positions[symbol])
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
                client.submit_order(order)
                msg = f"🔴 ALPACA SELL — {symbol}\nRSI: {rsi:.1f}\nPrice: ${price:.2f}\nQty: {qty}"
                print(msg)
                send_telegram(msg)

            else:
                print(f"  → HOLD (in_position={in_position})")

        except Exception as e:
            print(f"[ERR] {symbol}: {e}")

    send_telegram(f"⚪ Alpaca bot bežal | Equity: ${equity:,.2f}")
    print("Hotovo.")

if __name__ == "__main__":
    main()
