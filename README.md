# Stock Market Dashboard & Automated Trading Bot

## Overview
Stock market analysis dashboard and automated RSI-based trading bot using Alpaca API and Yahoo Finance data.

## Projects

### 1. Stock Dashboard (`dashboard.py`)
Interactive Streamlit dashboard for any stock ticker.
- Real-time price data via Yahoo Finance
- MA20, MA50 moving averages
- RSI(14) indicator
- Volume analysis

**Live demo:** https://stockdashboard-bbe5uejxrcujjnuxmxpuhz.streamlit.app

### 2. RSI Backtest (`backtest_rsi.py`)
5-year backtest of RSI mean reversion strategy on US stocks.

**Strategy:** Buy when RSI < 35 (oversold), sell when RSI > 65 (overbought)

**Results (5 years, AAPL + MSFT + GOOGL):**

| Stock | EV/trade | Winrate | Cumulative | Max DD |
|-------|----------|---------|------------|--------|
| AAPL | +3.93% | 82.6% | +90.3% | -14.4% |
| MSFT | +1.79% | 64.7% | +30.4% | -16.5% |
| GOOGL | +4.35% | 70.6% | +74.0% | -21.2% |
| **Combined** | **+3.41%** | **73.7%** | **+194.6%** | - |

### 3. Alpaca Paper Trading Bot (`alpaca_bot.py`)
Automated trading bot running on VPS (Hetzner, Helsinki).
- Runs every weekday at 15:30 UTC (US market hours)
- Paper trading via Alpaca API ($100,000 simulated)
- Telegram notifications on every trade
- Symbols: AAPL, MSFT, GOOGL

## Tech Stack
Python, pandas, numpy, yfinance, alpaca-py, Streamlit, Plotly, VPS (Hetzner)
