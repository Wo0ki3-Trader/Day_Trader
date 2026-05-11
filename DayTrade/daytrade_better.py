import streamlit as st
from streamlit_autorefresh import st_autorefresh

import yfinance as yf
import pandas as pd
import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Analyst Edge Pro",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# AUTO REFRESH
# =========================================================

st_autorefresh(interval=30000, key="market_refresh")

# =========================================================
# SESSION STATE
# =========================================================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        "NVDA",
        "SPY",
        "TSLA",
        "AMD",
        "PLTR",
        "META",
        "AAPL"
    ]

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🔍 Analyst Edge Pro")

new_ticker = st.sidebar.text_input(
    "Add Ticker",
    placeholder="AMD, PLTR, NVDA..."
).upper()

if st.sidebar.button("➕ Add"):
    if new_ticker:
        if new_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_ticker)
            st.sidebar.success(f"{new_ticker} added.")
        else:
            st.sidebar.warning("Ticker already exists.")

# Remove ticker
remove_ticker = st.sidebar.selectbox(
    "Remove Ticker",
    ["None"] + st.session_state.watchlist
)

if st.sidebar.button("❌ Remove"):
    if remove_ticker != "None":
        st.session_state.watchlist.remove(remove_ticker)
        st.sidebar.success(f"{remove_ticker} removed.")

# =========================================================
# DATA ENGINE
# =========================================================

@st.cache_data(ttl=60)
def get_master_data(symbol):

    try:
        ticker = yf.Ticker(symbol)

        df = ticker.history(
            period="1d",
            interval="5m",
            auto_adjust=True,
            prepost=True
        )

        if df.empty:
            return None, None

        # =================================================
        # INDICATORS
        # =================================================

        # EMAs
        df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

        # VWAP
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        df["VWAP"] = (
            (typical_price * df["Volume"]).cumsum()
            / df["Volume"].cumsum()
        )

        # Support / Resistance
        df["Resistance"] = df["High"].rolling(30).max()
        df["Support"] = df["Low"].rolling(30).min()

        # RSI
        delta = df["Close"].diff()

        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        gain = pd.Series(gain).rolling(14).mean()
        loss = pd.Series(loss).rolling(14).mean()

        rs = gain / loss.replace(0, 0.0001)

        df["RSI"] = 100 - (100 / (1 + rs.values))

        # MACD
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()

        df["MACD"] = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # Volume Spike
        df["AvgVolume"] = df["Volume"].rolling(20).mean()
        df["VolumeSpike"] = (
            df["Volume"] > (df["AvgVolume"] * 2)
        )

        # Daily Change %
        df["PctChange"] = (
            (df["Close"] - df["Close"].iloc[0])
            / df["Close"].iloc[0]
        ) * 100

        # News
        try:
            news = ticker.news
        except:
            news = []

        return df, news

    except Exception as e:
        st.error(f"Error loading {symbol}: {e}")
        return None, None

# =========================================================
# HEADER
# =========================================================

st.title("📈 Analyst Edge Pro")
st.caption(
    "Advanced Real-Time Trading Intelligence Dashboard"
)

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3 = st.tabs([
    "🎯 Market Scanner",
    "📊 Deep Dive",
    "📰 News Intelligence"
])

# =========================================================
# TAB 1 — SCANNER
# =========================================================

with tab1:

    st.subheader("Real-Time Technical Rankings")

    results = []

    for symbol in st.session_state.watchlist:

        df, _ = get_master_data(symbol)

        if df is not None and len(df) > 50:

            last = df.iloc[-1]

            score = 0

            # EMA Trend
            if last["EMA9"] > last["EMA20"]:
                score += 20

            # Above VWAP
            if last["Close"] > last["VWAP"]:
                score += 20

            # RSI Healthy
            if 45 < last["RSI"] < 70:
                score += 20

            # MACD Bullish
            if last["MACD"] > last["Signal"]:
                score += 20

            # Volume Spike
            if last["VolumeSpike"]:
                score += 20

            # Trade Signal
            if score >= 80:
                signal = "🔥 Strong Bullish"
            elif score >= 60:
                signal = "🟢 Bullish"
            elif score >= 40:
                signal = "🟡 Neutral"
            else:
                signal = "🔴 Weak"

            results.append({
                "Ticker": symbol,
                "Price": round(last["Close"], 2),
                "Score": score,
                "Signal": signal,
                "RSI": round(last["RSI"], 1),
                "VWAP": round(last["VWAP"], 2),
                "Support": round(last["Support"], 2),
                "Resistance": round(last["Resistance"], 2),
                "% Change": round(last["PctChange"], 2)
            })

    if results:

        results_df = pd.DataFrame(results)

        results_df = results_df.sort_values(
            "Score",
            ascending=False
        )

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning("No valid market data available.")

# =========================================================
# TAB 2 — DEEP DIVE
# =========================================================

with tab2:

    selected = st.selectbox(
        "Focus Asset",
        st.session_state.watchlist
    )

    df, _ = get_master_data(selected)

    if df is not None:

        last = df.iloc[-1]

        # =============================================
        # METRICS
        # =============================================

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Current Price",
            f"${last['Close']:.2f}"
        )

        c2.metric(
            "RSI",
            f"{last['RSI']:.1f}"
        )

        c3.metric(
            "Support",
            f"${last['Support']:.2f}"
        )

        c4.metric(
            "Resistance",
            f"${last['Resistance']:.2f}"
        )

        # =============================================
        # CHART
        # =============================================

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.6, 0.2, 0.2],
            vertical_spacing=0.03
        )

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price"
            ),
            row=1,
            col=1
        )

        # EMAs
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["EMA9"],
                name="EMA9"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["EMA20"],
                name="EMA20"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["VWAP"],
                name="VWAP"
            ),
            row=1,
            col=1
        )

        # Support / Resistance
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Resistance"],
                name="Resistance",
                line=dict(dash="dash")
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Support"],
                name="Support",
                line=dict(dash="dash")
            ),
            row=1,
            col=1
        )

        # RSI
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                name="RSI"
            ),
            row=2,
            col=1
        )

        # MACD
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MACD"],
                name="MACD"
            ),
            row=3,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Signal"],
                name="Signal"
            ),
            row=3,
            col=1
        )

        fig.update_layout(
            template="plotly_dark",
            height=950,
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =============================================
        # TRADE ANALYSIS
        # =============================================

        st.subheader("📌 AI Trade Read")

        bullish = (
            last["EMA9"] > last["EMA20"]
            and last["MACD"] > last["Signal"]
            and last["Close"] > last["VWAP"]
        )

        if bullish:
            st.success(
                "Bullish momentum detected. "
                "Trend, MACD, and VWAP alignment support continuation."
            )
        else:
            st.warning(
                "Mixed or bearish conditions detected. "
                "Wait for stronger confirmation."
            )

# =========================================================
# TAB 3 — NEWS
# =========================================================

with tab3:

    st.subheader(f"Latest Headlines — {selected}")

    _, news = get_master_data(selected)

    if news and isinstance(news, list):

        for item in news[:10]:

            content = item.get("content", {})

            title = (
                item.get("title")
                or content.get("title")
                or "No Title Available"
            )

            link = (
                item.get("link")
                or content.get("canonicalUrl", {}).get("url")
                or "#"
            )

            publisher = (
                item.get("publisher")
                or content.get("provider", {}).get("displayName")
                or "Unknown Source"
            )

            summary = (
                item.get("summary")
                or content.get("summary")
                or ""
            )

            pub_time = item.get("providerPublishTime")

            try:
                if pub_time:
                    dt = datetime.fromtimestamp(pub_time)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                else:
                    formatted_time = "Unknown Time"
            except:
                formatted_time = "Unknown Time"

            st.markdown(f"### [{title}]({link})")

            col1, col2 = st.columns(2)

            with col1:
                st.caption(f"📰 {publisher}")

            with col2:
                st.caption(f"🕒 {formatted_time}")

            if summary:
                st.write(summary)

            st.divider()

    else:
        st.info("No recent news found.")

# =========================================================
# FOOTER
# =========================================================

st.caption(
    "⚡ Auto-refreshing every 30 seconds | "
    "Built with Streamlit + yFinance + Plotly"
)