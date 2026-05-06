import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from alpaca.trading.client import TradingClient

st.set_page_config(page_title="Alpaca Trading Bot", page_icon="🤖", layout="wide")

st.title("🤖 Alpaca RSI Trading Bot")
st.caption("Automated paper trading — RSI mean reversion on AAPL, MSFT, GOOGL")

# ── CONFIG ────────────────────────────────────────────────────────────────────

API_KEY = "PKXBR37EUJIDZ6TEDR57272UZ3"
SECRET  = "EomZsLEN3KXWTVxeGPFggq8Wj8fLNjcZJ9FQXrXvqAsN"
SYMBOLS = ["AAPL", "MSFT", "GOOGL"]

# ── DATA ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_rsi_data(symbol):
    df = yf.download(symbol, period="60d", auto_adjust=True, progress=False)
    if df.empty:
        return 50.0, 0.0
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"].dropna()
    if len(close) < 15:
        return 50.0, float(close.iloc[-1]) if len(close) > 0 else 0.0
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean().replace(0, float("nan"))
    rsi   = (100 - 100 / (1 + gain / loss)).dropna()
    return float(rsi.iloc[-1]), float(close.iloc[-1])

@st.cache_data(ttl=300)
def get_account():
    client = TradingClient(API_KEY, SECRET, paper=True)
    account = client.get_account()
    positions = client.get_all_positions()
    return account, positions

# ── ACCOUNT ───────────────────────────────────────────────────────────────────

try:
    account, positions = get_account()
    equity    = float(account.equity)
    cash      = float(account.cash)
    pl        = float(account.equity) - 100000

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Portfolio Value", f"${equity:,.2f}")
    col2.metric("Cash", f"${cash:,.2f}")
    col3.metric("P&L vs Start", f"${pl:+,.2f}", f"{pl/1000:.2f}%")
    col4.metric("Account", "Paper Trading")
except Exception as e:
    st.error(f"Cannot connect to Alpaca: {e}")
    st.stop()

st.divider()

# ── RSI STATUS ────────────────────────────────────────────────────────────────

st.subheader("Current RSI Status")

pos_dict = {p.symbol: float(p.qty) for p in positions}

cols = st.columns(3)
for col, symbol in zip(cols, SYMBOLS):
    rsi, price = get_rsi_data(symbol)
    in_pos = symbol in pos_dict

    with col:
        if rsi < 35:
            status = "🟢 BUY ZONE"
            color  = "success"
        elif rsi > 65:
            status = "🔴 SELL ZONE"
            color  = "error"
        else:
            status = "⚪ NEUTRAL"
            color  = "info"

        if color == "success":
            st.success(f"**{symbol}**\n\nRSI: {rsi:.1f}\n\nPrice: ${price:.2f}\n\n{status}\n\nPosition: {'YES' if in_pos else 'NO'}")
        elif color == "error":
            st.error(f"**{symbol}**\n\nRSI: {rsi:.1f}\n\nPrice: ${price:.2f}\n\n{status}\n\nPosition: {'YES' if in_pos else 'NO'}")
        else:
            st.info(f"**{symbol}**\n\nRSI: {rsi:.1f}\n\nPrice: ${price:.2f}\n\n{status}\n\nPosition: {'YES' if in_pos else 'NO'}")

st.divider()

# ── RSI CHART ─────────────────────────────────────────────────────────────────

st.subheader("RSI History")

selected = st.selectbox("Select stock", SYMBOLS)

df = yf.download(selected, period="60d", auto_adjust=True, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
close = df["Close"].dropna()
delta = close.diff()
gain  = delta.clip(lower=0).rolling(14).mean()
loss  = (-delta.clip(upper=0)).rolling(14).mean().replace(0, float("nan"))
rsi_series = 100 - 100 / (1 + gain / loss)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=rsi_series, name="RSI", line=dict(color="#c77dff", width=2)))
fig.add_hline(y=65, line_dash="dash", line_color="#e63946", annotation_text="Sell (65)")
fig.add_hline(y=35, line_dash="dash", line_color="#06d6a0", annotation_text="Buy (35)")
fig.add_hrect(y0=35, y1=0, fillcolor="#06d6a0", opacity=0.05)
fig.add_hrect(y0=65, y1=100, fillcolor="#e63946", opacity=0.05)
fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(range=[0,100]))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── BACKTEST RESULTS ──────────────────────────────────────────────────────────

st.subheader("Backtest Results (5 years)")

bt = pd.DataFrame([
    {"Stock": "AAPL", "EV/trade": "+3.93%", "Winrate": "82.6%", "Cumulative": "+90.3%", "Max DD": "-14.4%"},
    {"Stock": "MSFT", "EV/trade": "+1.79%", "Winrate": "64.7%", "Cumulative": "+30.4%", "Max DD": "-16.5%"},
    {"Stock": "GOOGL","EV/trade": "+4.35%", "Winrate": "70.6%", "Cumulative": "+74.0%", "Max DD": "-21.2%"},
    {"Stock": "Combined","EV/trade": "+3.41%","Winrate": "73.7%","Cumulative": "+194.6%","Max DD": "-"},
])
st.dataframe(bt, use_container_width=True, hide_index=True)
st.caption("Strategy: Buy RSI < 35 | Sell RSI > 65 | No leverage")
