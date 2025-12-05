import streamlit as st
import yfinance as yf
import pandas as pd
import time
import random

st.set_page_config(page_title="Global Valuation Screener", page_icon="📈")
st.title("🌍 Global Stock Valuation Screener (Educational)")
st.caption("Compare metrics for US, NSE, BSE & global stocks. Not financial advice.")

# Mandatory Disclaimer
st.warning("""
**Disclaimer**: This tool is for **educational purposes only**.  
It does **not** constitute investment advice.  
Trading involves high risk. Consult a **SEBI-registered advisor** before acting.
""")

# User input
ticker_input = st.text_input("Enter Stock Ticker (e.g., TCS, RELIANCE, INFY, AAPL)", "RELIANCE")

if ticker_input:
    # Clean input
    base_ticker = ticker_input.strip().upper()
    
    # Auto-append .NS for Indian tickers that don't have exchange suffix
    if not base_ticker.endswith(('.NS', '.BO', '.T', '.L')):
        # Assume Indian stock if no suffix — try NSE first, then BSE
        candidates = [f"{base_ticker}.NS", f"{base_ticker}.BO"]
    elif base_ticker.endswith('.NS') or base_ticker.endswith('.BO'):
        candidates = [base_ticker]
    else:
        # US/global stock — use as-is
        candidates = [base_ticker]

    @st.cache_data(ttl=3600)
    def fetch_with_retry(ticker, max_retries=2):
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                # Check if valid (Yahoo returns empty dict or error for invalid tickers)
                if info and 'symbol' in info:
                    hist = stock.history(period="1d")
                    price = hist['Close'].iloc[-1] if len(hist) > 0 else "N/A"
                    return info, price, ticker
            except Exception as e:
                if attempt == max_retries - 1:
                    return None, str(e), ticker
            time.sleep(1 + random.uniform(0, 0.5))
        return None, "Max retries exceeded", ticker

    info, current_price, used_ticker = None, "N/A", None

    # Try each candidate (e.g., RELIANCE.NS → RELIANCE.BO)
    for ticker in candidates:
        with st.spinner(f"Trying {ticker}..."):
            info, current_price, used_ticker = fetch_with_retry(ticker)
            if info is not None:
                break

    if info is None:
        st.error("❌ No data found. Try:")
        st.markdown("""
        - **NSE**: `RELIANCE`, `TCS`, `HDFCBANK`  
        - **BSE**: `INFY`, `SBIN`  
        - **US**: `AAPL`, `MSFT`
        """)
        st.info("💡 Tip: For Indian stocks, just type the name (e.g., 'TCS') — we auto-add .NS/.BO")
        st.stop()

    # Display results
    company_name = info.get("longName", used_ticker)
    exchange = info.get("exchange", "N/A")
    st.subheader(f"{company_name} • {used_ticker}")
    st.metric("Current Price", f"₹{current_price:.2f}" if isinstance(current_price, float) else current_price)

    # Valuation metrics
    st.subheader("Valuation Metrics (Latest)")
    metrics_list = [
        ("P/E Ratio", info.get("trailingPE", "N/A")),
        ("P/B Ratio", info.get("priceToBook", "N/A")),
        ("PEG Ratio", info.get("pegRatio", "N/A")),
        ("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get("dividendYield") else "N/A"),
        ("50-Day MA", info.get("fiftyDayAverage", "N/A")),
        ("200-Day MA", info.get("twoHundredDayAverage", "N/A"))
    ]
    df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
    st.table(df)

    # Insights
    st.subheader("Educational Insights")
    pe = info.get("trailingPE", 1000)
    pb = info.get("priceToBook", 1000)
    peg = info.get("pegRatio", 1000)

    insights = []
    if pe < 15: insights.append("✅ P/E suggests undervaluation")
    elif pe > 25: insights.append("⚠️ P/E suggests overvaluation")
    if pb < 1.5: insights.append("✅ P/B suggests asset-backed value")
    elif pb > 3: insights.append("⚠️ P/B suggests premium pricing")
    if peg < 1: insights.append("✅ PEG < 1: growth may be undervalued")
    elif peg > 2: insights.append("⚠️ PEG > 2: growth may be overpriced")

    for msg in insights or ["No strong valuation signals detected."]:
        st.info(msg)

# Ticker Guide
st.markdown("---")
st.subheader("How to Use (India-Friendly)")
st.markdown("""
- **Just type the stock name** → we auto-add `.NS` or `.BO`  
  → e.g., `RELIANCE` → tries `RELIANCE.NS` then `RELIANCE.BO`
- **Or specify exchange**:  
  - NSE: `TCS.NS`  
  - BSE: `INFY.BO`
- **Global stocks**: `AAPL` (US), `7203.T` (Japan)
""")

st.caption("Data: Yahoo Finance (free) | Covers NSE, BSE, NYSE, NASDAQ | Educational Use Only")
