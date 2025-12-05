import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Global Valuation Screener", page_icon="📈")
st.title("🌍 Global Stock Valuation Screener (Educational)")
st.caption("Compare metrics across global stocks. Not financial advice.")

# Mandatory Disclaimer
st.warning("""
**Disclaimer**: This tool is for **educational purposes only**.  
It does **not** constitute investment advice.  
Trading involves high risk. Consult a **SEBI-registered advisor** before acting.
""")

# User input
ticker_input = st.text_input("Enter Global Stock Ticker (e.g., AAPL, RELIANCE.NS, 7203.T)", "AAPL")

if ticker_input:
    # Normalize ticker: handle mixed case (e.g., 'tcs.ns' → 'TCS.NS')
    ticker_clean = ticker_input.strip()
    if ticker_clean.lower().endswith('.ns') and not ticker_clean.endswith('.NS'):
        ticker_clean = ticker_clean[:-3] + '.NS'
    elif ticker_clean.lower().endswith('.bo') and not ticker_clean.endswith('.BO'):
        ticker_clean = ticker_clean[:-3] + '.BO'
    ticker = ticker_clean.upper()

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_stock_data(ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1d")
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else "N/A"
            return info, current_price
        except Exception as e:
            return None, f"Error: {str(e)}"

    with st.spinner(f"Fetching data for {ticker}..."):
        info, current_price = get_stock_data(ticker)

        if info is None:
            st.error(current_price)  # Show error message
            st.info("Try a different ticker like `AAPL`, `TCS.NS`, or `RELIANCE.NS`.")
            st.stop()

        # Get company name and exchange
        company_name = info.get("longName", ticker)
        exchange = info.get("exchange", "N/A")

        # Display header
        st.subheader(f"{company_name} ({ticker}) • {exchange}")
        st.metric("Current Price", f"${current_price:.2f}" if isinstance(current_price, float) else current_price)

        # Valuation metrics from Yahoo Finance
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

        # Educational insights
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

# Ticker guide
st.markdown("---")
st.subheader("How to Use Tickers")
st.markdown("""
- **🇺🇸 US Stocks**: `AAPL`, `MSFT`
- **🇮🇳 Indian Stocks**: `TCS.NS`, `RELIANCE.NS`, `INFY.BO`
- **🇯🇵 Japan**: `7203.T`
- **🇬🇧 UK**: `VOD.L`
""")

st.caption("Data: Yahoo Finance (free) | Educational Use Only")
