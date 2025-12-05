import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import os

# Load API key securely from Streamlit Cloud Secrets
FMP_API_KEY = os.getenv("FMP_API_KEY")

# If no key is found (e.g., during local dev), allow fallback with warning
if not FMP_API_KEY:
    st.warning("⚠️ FMP_API_KEY not set. Using limited Yahoo Finance data only.")
    FMP_API_KEY = "dummy_key"  # Prevent crashes, but FMP calls will fail

FMP_BASE = "https://financialmodelingprep.com/api/v3"

st.set_page_config(page_title="Global Valuation Screener", page_icon="📈")
st.title("🌍 Global Stock Valuation Screener (Educational)")
st.caption("Compare valuation metrics across global stocks. Not financial advice.")

# 🔒 Mandatory Disclaimer
st.warning("""
**Disclaimer**: This tool is for **educational purposes only**.  
It does **not** constitute investment advice.  
Trading involves high risk. Consult a **SEBI-registered advisor** before acting.
""")

# User input
ticker_input = st.text_input("Enter Global Stock Ticker", "AAPL")

if ticker_input:
    # 🔤 Normalize ticker: handle mixed case (e.g., 'tcs.ns' → 'TCS.NS')
    ticker_clean = ticker_input.strip()
    if ticker_clean.lower().endswith('.ns') and not ticker_clean.endswith('.NS'):
        ticker_clean = ticker_clean[:-3] + '.NS'
    elif ticker_clean.lower().endswith('.bo') and not ticker_clean.endswith('.BO'):
        ticker_clean = ticker_clean[:-3] + '.BO'
    ticker = ticker_clean.upper()

    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            # 📡 Fetch from FMP (if API key is valid)
            has_fmp_data = False
            profile = None
            metrics = None

            if FMP_API_KEY != "dummy_key":
                # Get profile
                profile_url = f"{FMP_BASE}/profile/{ticker}?apikey={FMP_API_KEY}"
                profile_res = requests.get(profile_url, timeout=10)
                
                if profile_res.status_code == 200:
                    profile_data = profile_res.json()
                    if profile_data:
                        profile = profile_data[0]
                        # Get metrics
                        metrics_url = f"{FMP_BASE}/key-metrics/{ticker}?apikey={FMP_API_KEY}"
                        metrics_res = requests.get(metrics_url, timeout=10)
                        if metrics_res.status_code == 200:
                            metrics_data = metrics_res.json()
                            if metrics_data:
                                metrics = metrics_data[0]
                                has_fmp_data = True
                elif profile_res.status_code == 403:
                    st.error("❌ Your FMP API key is invalid or rate-limited (250 calls/day).")
                    st.info("Visit: https://financialmodelingprep.com/developer/docs to get a new key.")
                    st.stop()

            # 📈 Get price from Yahoo Finance (always works)
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(period="1d")
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else "N/A"

            # Display company info
            company_name = profile["companyName"] if profile else ticker
            exchange = profile["exchangeShortName"] if profile else "Yahoo Finance"
            st.subheader(f"{company_name} ({ticker}) • {exchange}")
            st.metric("Current Price", f"${current_price:.2f}" if isinstance(current_price, float) else current_price)

            # Valuation metrics
            st.subheader("Valuation Metrics (Latest)")
            def safe_round(val, decimals=2):
                return round(val, decimals) if isinstance(val, (int, float)) and val is not None else "N/A"

            metrics_list = [
                ("P/E Ratio", safe_round(metrics.get("peRatio") if metrics else None)),
                ("P/B Ratio", safe_round(metrics.get("priceToBookRatio") if metrics else None)),
                ("PEG Ratio", safe_round(metrics.get("pegRatio") if metrics else None)),
                ("Dividend Yield", 
                 f"{metrics.get('dividendYield', 0)*100:.2f}%" if metrics and metrics.get('dividendYield') else "N/A"),
                ("50-Day MA", safe_round(metrics.get("priceTo50DayMovingAverage") if metrics else None)),
                ("200-Day MA", safe_round(metrics.get("priceTo200DayMovingAverage") if metrics else None)),
            ]

            df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
            st.table(df)

            # Insights (only if FMP data available)
            if metrics:
                st.subheader("Educational Insights")
                pe = metrics.get("peRatio", 1000)
                pb = metrics.get("priceToBookRatio", 1000)
                peg = metrics.get("pegRatio", 1000)

                insights = []
                if pe < 15: insights.append("✅ P/E suggests undervaluation")
                elif pe > 25: insights.append("⚠️ P/E suggests overvaluation")
                if pb < 1.5: insights.append("✅ P/B suggests asset-backed value")
                elif pb > 3: insights.append("⚠️ P/B suggests premium pricing")
                if peg < 1: insights.append("✅ PEG < 1: growth may be undervalued")
                elif peg > 2: insights.append("⚠️ PEG > 2: growth may be overpriced")

                for msg in insights or ["No strong valuation signals detected."]:
                    st.info(msg)
            else:
                st.info("💡 Valuation insights require FMP data (add a valid API key in secrets).")

        except Exception as e:
            st.error(f"🚨 Error: {str(e)}")
            st.info("Try a valid ticker like `AAPL`, `TCS.NS`, or `RELIANCE.NS`.")

# 🌐 Ticker guide
st.markdown("---")
st.subheader("Global Ticker Examples")
st.markdown("""
- **🇺🇸 US**: `AAPL`, `MSFT`
- **🇮🇳 India**: `TCS.NS`, `RELIANCE.NS`, `INFY.BO`
- **🇯🇵 Japan**: `7203.T`
- **🇬🇧 UK**: `VOD.L`
""")

st.caption("Data: Yahoo Finance (free) + Financial Modeling Prep (with API key) | Educational Use Only")
