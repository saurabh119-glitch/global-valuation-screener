import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

st.set_page_config(page_title="NSE Valuation Screener", page_icon="📈")
st.title("🇮🇳 NSE Stock Valuation Screener (Educational)")
st.caption("Compare metrics for NSE-listed stocks using official NSE data. Not financial advice.")

# Mandatory Disclaimer
st.warning("""
**Disclaimer**: This tool is for **educational purposes only**.  
It does **not** constitute investment advice.  
Trading involves high risk. Consult a **SEBI-registered advisor** before acting.
""")

# User input
ticker_input = st.text_input("Enter NSE Stock Symbol (e.g., RELIANCE, TCS, HDFCBANK)", "RELIANCE")

if ticker_input:
    # Normalize ticker: uppercase, strip spaces
    symbol = ticker_input.strip().upper()
    
    @st.cache_data(ttl=3600)
    def scrape_nse_data(symbol):
        url = f"https://www.nseindia.com/get-quote/equity/{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        try:
            session = requests.Session()
            session.headers.update(headers)
            
            # First, get cookies by visiting homepage
            session.get("https://www.nseindia.com", timeout=10)
            
            # Then fetch quote page
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key metrics
            data = {}
            
            # Current Price
            price_elem = soup.find('div', class_='last-price')
            if price_elem:
                data['current_price'] = price_elem.get_text(strip=True).replace(',', '')
            
            # P/E Ratio (Adjusted P/E)
            pe_elem = soup.find('div', text=lambda x: x and 'Adjusted P/E' in x)
            if pe_elem:
                pe_value = pe_elem.find_next('div').get_text(strip=True)
                data['pe_ratio'] = pe_value.replace(',', '') if pe_value.replace(',', '').replace('.', '').isdigit() else "N/A"
            
            # Market Cap
            mc_elem = soup.find('div', text=lambda x: x and 'Total Market Cap' in x)
            if mc_elem:
                mc_value = mc_elem.find_next('div').get_text(strip=True)
                data['market_cap'] = mc_value
            
            # 52 Week High & Low
            high_elem = soup.find('div', text=lambda x: x and '52 Week High' in x)
            low_elem = soup.find('div', text=lambda x: x and '52 Week Low' in x)
            if high_elem:
                data['52w_high'] = high_elem.find_next('div').get_text(strip=True)
            if low_elem:
                data['52w_low'] = low_elem.find_next('div').get_text(strip=True)
            
            # Trading Status
            status_elem = soup.find('div', text=lambda x: x and 'Trading Status' in x)
            if status_elem:
                data['trading_status'] = status_elem.find_next('div').get_text(strip=True)
            
            return data
            
        except Exception as e:
            return None

    with st.spinner(f"Fetching data for {symbol}..."):
        nse_data = scrape_nse_data(symbol)
        
        if not nse_data:
            st.error("❌ Data not found. Try:")
            st.markdown("""
            - **Valid NSE symbols**: `RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `SBIN`
            - Avoid `.NS` suffix — just use `TCS`, not `TCS.NS`
            """)
            st.stop()

        # Display header
        st.subheader(f"{symbol} • NSE")
        st.metric("Current Price", f"₹{nse_data.get('current_price', 'N/A')}")

        # Valuation Metrics
        st.subheader("Valuation Metrics (Official NSE Data)")
        metrics_list = [
            ("P/E Ratio", nse_data.get("pe_ratio", "N/A")),
            ("Market Cap", nse_data.get("market_cap", "N/A")),
            ("52-Week High", nse_data.get("52w_high", "N/A")),
            ("52-Week Low", nse_data.get("52w_low", "N/A")),
            ("Trading Status", nse_data.get("trading_status", "N/A"))
        ]
        df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
        st.table(df)

        # Educational Insights
        st.subheader("Educational Insights")
        pe = nse_data.get("pe_ratio", "N/A")
        if isinstance(pe, str) and pe.replace('.', '').isdigit():
            pe = float(pe)
            if pe < 15:
                st.info("✅ P/E suggests undervaluation")
            elif pe > 25:
                st.info("⚠️ P/E suggests overvaluation")
        else:
            st.info("📊 P/E data not available")

# Ticker Guide
st.markdown("---")
st.subheader("How to Use (NSE Only)")
st.markdown("""
- **Enter NSE symbol only** → e.g., `RELIANCE`, `TCS`, `HDFCBANK`
- **No .NS suffix needed** — we auto-detect NSE
- **Not for BSE or global stocks** — this is NSE-only
""")

st.caption("Data: NSE India (official) | Educational Use Only")
