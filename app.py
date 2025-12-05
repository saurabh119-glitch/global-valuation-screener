import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import os  # ← Add this

# ✅ Load API key from Streamlit Cloud Secrets (secure!)
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Handle missing key gracefully
if not FMP_API_KEY:
    st.error("❌ FMP_API_KEY is not set. Please add it in Streamlit Cloud → App Settings → Secrets")
    st.stop()

FMP_BASE = "https://financialmodelingprep.com/api/v3"  # ← Removed extra space

st.set_page_config(page_title="Global Valuation Screener", page_icon="📈")
st.title("🌍 Global Stock Valuation Screener (Educational)")
st.caption("Compare valuation metrics across 5000+ global stocks. Not financial advice.")

# Disclaimer (MUST HAVE)
st.warning("""
**Disclaimer**: This tool is for educational purposes only. 
It does not constitute investment advice. 
Trading stocks involves significant risk. Consult a SEBI-registered advisor before making decisions.
""")

# Stock input
ticker = st.text_input("Enter Global Stock Ticker (e.g., AAPL, RELIANCE.NS, 7203.T)", "AAPL")

if ticker:
    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            # 1. Get company profile from FMP
            profile_url = f"{FMP_BASE}/profile/{ticker}?apikey={FMP_API_KEY}"  # ← Use FMP_API_KEY
            profile = requests.get(profile_url).json()
            
            if not profile:
                st.error("Stock not found in global database. Try .NS for Indian stocks (e.g., RELIANCE.NS)")
                st.stop()
            
            profile = profile[0]
            company_name = profile["companyName"]
            exchange = profile["exchangeShortName"]
            
            # 2. Get key metrics
            metrics_url = f"{FMP_BASE}/key-metrics/{ticker}?apikey={FMP_API_KEY}"  # ← Use FMP_API_KEY
            metrics = requests.get(metrics_url).json()
            
            if not metrics:
                st.error("Valuation data unavailable for this stock.")
                st.stop()
            
            m = metrics[0]
            
            # 3. Get current price from Yahoo Finance (fallback)
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else m.get("price", "N/A")
            
            # Display
            st.subheader(f"{company_name} ({ticker}) • {exchange}")
            st.metric("Current Price", f"${current_price:.2f}" if isinstance(current_price, float) else current_price)
            
            # Valuation table
            st.subheader("Valuation Metrics (Latest)")
            metrics_data = {
                "Metric": ["P/E Ratio", "P/B Ratio", "PEG Ratio", "Dividend Yield", "50-Day MA", "200-Day MA"],
                "Value": [
                    round(m.get("peRatio", 0), 2) if m.get("peRatio") else "N/A",
                    round(m.get("priceToBookRatio", 0), 2) if m.get("priceToBookRatio") else "N/A",
                    round(m.get("pegRatio", 0), 2) if m.get("pegRatio") else "N/A",
                    f"{m.get('dividendYield', 0)*100:.2f}%" if m.get("dividendYield") else "N/A",
                    round(m.get("priceTo50DayMovingAverage", 0), 2) if m.get("priceTo50DayMovingAverage") else "N/A",
                    round(m.get("priceTo200DayMovingAverage", 0), 2) if m.get("priceTo200DayMovingAverage") else "N/A"
                ]
            }
            df = pd.DataFrame(metrics_data)
            st.table(df)
            
            # Educational interpretation (NOT advice)
            st.subheader("Educational Insights")
            pe = m.get("peRatio", 1000)
            pb = m.get("priceToBookRatio", 1000)
            peg = m.get("pegRatio", 1000)
            
            insights = []
            if pe < 15:
                insights.append("✅ P/E suggests undervaluation (vs historical avg)")
            elif pe > 25:
                insights.append("⚠️ P/E suggests overvaluation (vs historical avg)")
            
            if pb < 1.5:
                insights.append("✅ P/B suggests asset-backed value")
            elif pb > 3:
                insights.append("⚠️ P/B suggests premium pricing")
                
            if peg < 1:
                insights.append("✅ PEG < 1: growth may be undervalued")
            elif peg > 2:
                insights.append("⚠️ PEG > 2: growth may be overpriced")
            
            if insights:
                for i in insights:
                    st.info(i)
            else:
                st.info("No strong valuation signals detected.")
                
        except Exception as e:
            st.error(f"Error: {e}. Try a different ticker (e.g., TCS.NS for Indian stocks).")

# Supported exchanges
st.markdown("---")
st.subheader("How to Use Tickers")
st.markdown("""
- **US Stocks**: `AAPL`, `MSFT`
- **Indian Stocks**: `RELIANCE.NS`, `TCS.NS`  
- **Japan**: `7203.T` (Toyota)
- **UK**: `VOD.L` (Vodafone)
""")

st.caption("Data: Financial Modeling Prep + Yahoo Finance | Free Tier")
