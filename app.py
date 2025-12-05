import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import os

# Load API key from Streamlit Cloud Secrets (secure!)
FMP_API_KEY = os.getenv("FMP_API_KEY")

if not FMP_API_KEY:
    st.error("❌ FMP_API_KEY is not set. Please add it in Streamlit Cloud → App Settings → Secrets")
    st.stop()

FMP_BASE = "https://financialmodelingprep.com/api/v3"

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
ticker_input = st.text_input("Enter Global Stock Ticket (e.g., AAPL, RELIANCE.NS, 7203.T)", "AAPL")

if ticker_input:
    # Clean and normalize ticker
    ticker_clean = ticker_input.strip()
    
    # Auto-correct common Indian exchange suffixes
    if ticker_clean.lower().endswith('.ns') and not ticker_clean.endswith('.NS'):
        ticker_clean = ticker_clean[:-3] + '.NS'
    elif ticker_clean.lower().endswith('.bo') and not ticker_clean.endswith('.BO'):
        ticker_clean = ticker_clean[:-3] + '.BO'
    
    # Final uppercase conversion
    ticker = ticker_clean.upper()
    
    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            # 1. Get company profile from FMP
            profile_url = f"{FMP_BASE}/profile/{ticker}?apikey={FMP_API_KEY}"
            profile_response = requests.get(profile_url)
            
            if profile_response.status_code != 200:
                st.error(f"❌ API Error: {profile_response.status_code}. Try a different ticker.")
                st.stop()
                
            profile_data = profile_response.json()
            
            if not profile_data:
                st.error(f"❌ Stock '{ticker}' not found. Try:")
                st.markdown("""
                - **Indian Stocks**: `TCS.NS`, `RELIANCE.NS`
                - **US Stocks**: `AAPL`, `MSFT`
                - **Japan**: `7203.T`
                """)
                st.stop()
            
            profile = profile_data[0]
            company_name = profile["companyName"]
            exchange = profile["exchangeShortName"]
            
            # 2. Get key metrics
            metrics_url = f"{FMP_BASE}/key-metrics/{ticker}?apikey={FMP_API_KEY}"
            metrics_response = requests.get(metrics_url)
            metrics_data = metrics_response.json() if metrics_response.status_code == 200 else []
            
            if not metrics_data:
                st.error("Valuation data unavailable for this stock.")
                st.stop()
            
            m = metrics_data[0]
            
            # 3. Get current price from Yahoo Finance
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else m.get("price", "N/A")
            
            # Display
            st.subheader(f"{company_name} ({ticker}) • {exchange}")
            st.metric("Current Price", f"${current_price:.2f}" if isinstance(current_price, float) else current_price)
            
            # Valuation table
            st.subheader("Valuation Metrics (Latest)")
            metrics_list = [
                ("P/E Ratio", round(m.get("peRatio"), 2) if m.get("peRatio") else "N/A"),
                ("P/B Ratio", round(m.get("priceToBookRatio"), 2) if m.get("priceToBookRatio") else "N/A"),
                ("PEG Ratio", round(m.get("pegRatio"), 2) if m.get("pegRatio") else "N/A"),
                ("Dividend Yield", f"{m.get('dividendYield', 0)*100:.2f}%" if m.get("dividendYield") else "N/A"),
                ("50-Day MA", round(m.get("priceTo50DayMovingAverage"), 2) if m.get("priceTo50DayMovingAverage") else "N/A"),
                ("200-Day MA", round(m.get("priceTo200DayMovingAverage"), 2) if m.get("priceTo200DayMovingAverage") else "N/A")
            ]
            
            df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
            st.table(df)
            
            # Educational interpretation
            st.subheader("Educational Insights")
            pe = m.get("peRatio", 1000)
            pb = m.get("priceToBookRatio", 1000)
            peg = m.get("pegRatio", 1000)
            
            insights = []
            if pe < 15: insights.append("✅ P/E suggests undervaluation")
            elif pe > 25: insights.append("⚠️ P/E suggests overvaluation")
            if pb < 1.5: insights.append("✅ P/B suggests asset-backed value")
            elif pb > 3: insights.append("⚠️ P/B suggests premium pricing")
            if peg < 1: insights.append("✅ PEG < 1: growth may be undervalued")
            elif peg > 2: insights.append("⚠️ PEG > 2: growth may be overpriced")
            
            for i in insights or ["No strong valuation signals detected."]:
                st.info(i)
                
        except Exception as e:
            st.error(f"🚨 Error: {str(e)}")
            st.info("Try a different ticker (e.g., TCS.NS, AAPL).")

# Supported exchanges
st.markdown("---")
st.subheader("How to Use Tickers")
st.markdown("""
- **US Stocks**: `AAPL`, `MSFT`
- **Indian Stocks**: `TCS.NS`, `RELIANCE.NS`  
- **Japan**: `7203.T`
- **UK**: `VOD.L`
""")

st.caption("Data: Financial Modeling Prep + Yahoo Finance | Free Tier")
