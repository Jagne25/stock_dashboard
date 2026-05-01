import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", page_icon="📊", layout="wide")

st.title("📊 Stock Market Dashboard")
st.caption("Real-time stock data powered by Yahoo Finance.")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    ticker  = st.text_input("Ticker symbol", value="AAPL").upper()
    period  = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    st.markdown("---")
    st.markdown("**Examples:** AAPL, TSLA, MSFT, GOOGL, BTC-USD, ETH-USD")

# ── DATA ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_data(ticker, period):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    df.columns = df.columns.get_level_values(0)
    df = df.dropna()

    # MA
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    # RSI(14)
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean().replace(0, np.nan)
    df["RSI"] = 100 - 100 / (1 + gain / loss)

    return df

try:
    df = load_data(ticker, period)
    info = yf.Ticker(ticker).info
except Exception as e:
    st.error(f"Cannot load data for {ticker}: {e}")
    st.stop()

if df.empty:
    st.error(f"No data found for {ticker}.")
    st.stop()

# ── METRICS ───────────────────────────────────────────────────────────────────

last  = float(df["Close"].iloc[-1])
prev  = float(df["Close"].iloc[-2])
chg   = last - prev
chg_p = chg / prev * 100
high  = float(df["High"].max())
low   = float(df["Low"].min())
name  = info.get("shortName", ticker)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(name, f"${last:,.2f}", f"{chg:+.2f} ({chg_p:+.1f}%)")
col2.metric("52w High", f"${high:,.2f}")
col3.metric("52w Low",  f"${low:,.2f}")
col4.metric("RSI(14)",  f"{df['RSI'].iloc[-1]:.1f}")
col5.metric("Volume",   f"{int(df['Volume'].iloc[-1]):,}")

st.divider()

# ── PRICE CHART ───────────────────────────────────────────────────────────────

fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    row_heights=[0.6, 0.2, 0.2],
                    vertical_spacing=0.03)

# Cena + MA
fig.add_trace(go.Scatter(x=df.index, y=df["Close"],
    name="Price", line=dict(color="#4895ef", width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MA20"],
    name="MA20", line=dict(color="#f77f00", width=1.2, dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MA50"],
    name="MA50", line=dict(color="#e63946", width=1.2, dash="dot")), row=1, col=1)

# Objem
fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
    name="Volume", marker_color="#4895ef", opacity=0.4), row=2, col=1)

# RSI
fig.add_trace(go.Scatter(x=df.index, y=df["RSI"],
    name="RSI", line=dict(color="#c77dff", width=1.5)), row=3, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="#e63946", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#06d6a0", row=3, col=1)

fig.update_layout(
    template="plotly_dark", height=600,
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", y=1.02),
    showlegend=True
)
fig.update_yaxes(title_text="Price ($)", row=1, col=1)
fig.update_yaxes(title_text="Volume",   row=2, col=1)
fig.update_yaxes(title_text="RSI",      row=3, col=1, range=[0, 100])

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── RAW DATA ──────────────────────────────────────────────────────────────────

with st.expander("Raw data (last 20 rows)"):
    st.dataframe(df[["Close","High","Low","Open","Volume","MA20","MA50","RSI"]].tail(20).round(2),
                 use_container_width=True)

st.caption("Data from Yahoo Finance · Refreshes every 5 minutes")
