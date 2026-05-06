"""
RSI Mean Reversion Backtest
Stratégia: kúp keď RSI < 35, predaj keď RSI > 65
Testujem na AAPL, TSLA, MSFT, GOOGL za 5 rokov
"""

import yfinance as yf
import pandas as pd
import numpy as np

SYMBOLS  = ["AAPL", "MSFT", "GOOGL"]
RSI_BUY  = 35   # kúp keď RSI pod toto
RSI_SELL = 65   # predaj keď RSI nad toto
PERIOD   = "5y"

# ── INDIKÁTORY ────────────────────────────────────────────────────────────────

def calc_rsi(close, period=14):
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean().replace(0, np.nan)
    return 100 - 100 / (1 + gain / loss)

# ── BACKTEST ──────────────────────────────────────────────────────────────────

def run_backtest(symbol):
    df = yf.download(symbol, period=PERIOD, auto_adjust=True, progress=False)
    df.columns = df.columns.get_level_values(0)
    df["RSI"] = calc_rsi(df["Close"])
    df = df.dropna().reset_index()

    trades = []
    in_trade = False

    for i in range(1, len(df)):
        row  = df.iloc[i]
        prev = df.iloc[i-1]

        if not in_trade:
            if prev["RSI"] < RSI_BUY:
                in_trade    = True
                entry_price = float(row["Close"])
                entry_date  = row["Date"]

        else:
            if prev["RSI"] > RSI_SELL:
                exit_price = float(row["Close"])
                pnl = (exit_price - entry_price) / entry_price * 100
                trades.append({
                    "entry": entry_date,
                    "exit":  row["Date"],
                    "entry_price": entry_price,
                    "exit_price":  exit_price,
                    "pnl": pnl,
                })
                in_trade = False

    if len(trades) == 0:
        return None

    t = pd.DataFrame(trades)
    wins   = t[t["pnl"] > 0]
    losses = t[t["pnl"] <= 0]
    ev     = t["pnl"].mean()
    winrate = len(wins) / len(t) * 100

    equity  = t["pnl"].cumsum()
    max_dd  = (equity - equity.cummax()).min()

    print(f"\n── {symbol} ──")
    print(f"  Obchody:   {len(t)}")
    print(f"  Winrate:   {winrate:.1f}%")
    print(f"  Avg win:   +{wins['pnl'].mean():.2f}%" if len(wins) > 0 else "  Avg win: N/A")
    print(f"  Avg loss:  {losses['pnl'].mean():.2f}%" if len(losses) > 0 else "  Avg loss: N/A")
    print(f"  EV:        {ev:+.2f}% na obchod")
    print(f"  Kumulatív: {equity.iloc[-1]:+.1f}%")
    print(f"  Max DD:    {max_dd:.1f}%")

    return t

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"RSI Mean Reversion Backtest")
    print(f"Buy RSI < {RSI_BUY} | Sell RSI > {RSI_SELL} | Period: {PERIOD}")

    all_trades = []
    for symbol in SYMBOLS:
        t = run_backtest(symbol)
        if t is not None:
            t["symbol"] = symbol
            all_trades.append(t)

    combined = pd.concat(all_trades, ignore_index=True)
    wins     = combined[combined["pnl"] > 0]
    losses   = combined[combined["pnl"] <= 0]
    ev       = combined["pnl"].mean()

    print(f"\n── COMBINED ──")
    print(f"  Obchody:   {len(combined)}")
    print(f"  Winrate:   {len(wins)/len(combined)*100:.1f}%")
    print(f"  EV:        {ev:+.2f}% na obchod")
    print(f"  Kumulatív: {combined['pnl'].sum():+.1f}%")
    print()
    if ev > 0:
        print("  → Pozitívny EV. Ideme na paper trading.")
    else:
        print("  → Negatívny EV. Treba upraviť parametre.")
