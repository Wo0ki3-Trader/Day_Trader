import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import time
from datetime import datetime

st.set_page_config(page_title="Quant Edge: Command Center", layout="wide")

# --- 1. SESSION STATE ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["GEN", "FLNC", "MRAM", "BW", "OXY", "NVDA", "SPY"]
if 'trade_ideas' not in st.session_state:
    st.session_state.trade_ideas = []

# --- 2. SIDEBAR: GLOBAL CONTROLS ---
st.sidebar.title("🎮 Command Controls")

# Dropdown for focused analysis
selected_ticker = st.sidebar.selectbox("🎯 Target Asset", st.session_state.watchlist)

# Manual Ticker Addition
new_ticker = st.sidebar.text_input("➕ Add New Ticker:").upper()
if st.sidebar.button("Add to Watchlist") and new_ticker:
    if new_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker)
        st.rerun()

refresh_rate = st.sidebar.slider("Refresh Interval (s)", 10, 60, 30)


# --- 3. THE ANALYST ENGINE ---
def get_pro_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="5m")
        if df.empty: return None, None

        # Technicals
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['Resistance'] = df['High'].rolling(window=30).max()
        df['Support'] = df['Low'].rolling(window=30).min()

        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        return df, ticker.news
    except:
        return None, None


# --- 4. TABBED INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Execution Scanner", "📊 Deep Dive", "💡 Gemini Hub", "📰 News"])

with tab1:
    st.subheader("Live Market Scanner")
    results = []
    for s in st.session_state.watchlist:
        df, _ = get_pro_data(s)
        if df is not None:
            last = df.iloc[-1]
            score = 0
            if last['EMA9'] > last['EMA20']: score += 25
            if last['Close'] > last['VWAP']: score += 25
            if last['Close'] > last['Support']: score += 25
            if 40 < last['RSI'] < 65: score += 25

            results.append({
                "Ticker": s, "Price": f"${last['Close']:.2f}",
                "Score": score, "RSI": round(last['RSI'], 1),
                "Floor": f"${last['Support']:.2f}", "Ceiling": f"${last['Resistance']:.2f}"
            })
    st.dataframe(pd.DataFrame(results).sort_values("Score", ascending=False), use_container_width=True, hide_index=True)

with tab2:
    st.subheader(f"Deep Dive Analysis: {selected_ticker}")
    df, _ = get_pro_data(selected_ticker)
    if df is not None:
        last = df.iloc[-1]

        # Dashboard metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Support", f"${last['Support']:.2f}")
        c2.metric("Resistance", f"${last['Resistance']:.2f}")
        c3.metric("RSI", f"{last['RSI']:.1f}")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                     name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Resistance'], name="Resist", line=dict(color='red', dash='dash')),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Support'], name="Supp", line=dict(color='green', dash='dash')),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='yellow')), row=2, col=1)

        fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("🤖 Gemini Intelligence Hub")
    raw_intel = st.text_area("Paste Today's Nasdaq Pre-Market Trade Ideas here:", height=200)

    if st.button("⚡ Sync & Parse Ideas"):
        if raw_intel:
            # Extract Tickers (Regex for 3-5 uppercase letters)
            found_tickers = re.findall(r'\b[A-Z]{3,5}\b', raw_intel)
            for t in found_tickers:
                if t not in st.session_state.watchlist:
                    st.session_state.watchlist.append(t)

            st.session_state.trade_ideas.append({"time": datetime.now().strftime("%H:%M"), "content": raw_intel})
            st.success(f"Success! Parsed Tickers: {', '.join(found_tickers)}. These have been added to your scanner.")
            st.rerun()

    st.divider()
    for idea in reversed(st.session_state.trade_ideas):
        st.info(f"**Imported at {idea['time']}**\n\n{idea['content']}")

with tab4:
    st.subheader(f"News Sentiment: {selected_ticker}")
    _, news = get_pro_data(selected_ticker)
    if news:
        for item in news[:5]:
            st.markdown(f"### [{item.get('title', 'Headline')}]({item.get('link', '#')})")
            st.caption(f"Source: {item.get('publisher')} | Type: {item.get('type')}")
            st.divider()
    else:
        st.write("No news found for this ticker.")

# Refresh Logic
time.sleep(refresh_rate)
st.rerun()

st.sidebar.divider()
st.sidebar.caption("⚠️ **Disclaimer:** This tool is for educational and analysis purposes only. "
                   "It is not financial advice. Day trading involves significant risk. "
                   "Always verify data before executing trades.")