import streamlit as st
import pandas as pd
import time
import random
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="NSE Valuation Screener", page_icon="📈")
st.title("🇮🇳 NSE Stock Valuation Screener (Educational)")
st.caption("Compare metrics for NSE-listed stocks using official Screener.in data. Not financial advice.")

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
    def scrape_screener_consolidated(symbol):
        # Convert to Screener format (e.g., RELIANCE → reliance)
        screener_id = symbol.lower()
        url = f"https://www.screener.in/company/{screener_id}/consolidated/"
        
        try:
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
            
            session = requests.Session()
            session.headers.update(headers)
            
            # First, get cookies by visiting homepage
            session.get("https://www.screener.in", timeout=10)
            
            # Then fetch consolidated page
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract company name
            company_name_elem = soup.find('h1', class_='company-name')
            company_name = company_name_elem.get_text(strip=True) if company_name_elem else symbol
            
            # Extract current price
            price_elem = soup.find('div', class_='company-price')
            current_price = price_elem.get_text(strip=True).replace('₹', '').replace(',', '') if price_elem else "N/A"
            
            # Extract metrics from "Ratios" section
            ratios_section = soup.find('section', id='ratios')
            if not ratios_section:
                return None
            
            metrics = {}
            
            # P/E Ratio
            pe_div = ratios_section.find('div', text=lambda x: x and 'Stock P/E' in x)
            if pe_div:
                pe_value = pe_div.find_next('div').get_text(strip=True)
                try:
                    metrics['pe_ratio'] = float(pe_value.replace(',', ''))
                except ValueError:
                    metrics['pe_ratio'] = "N/A"
            
            # P/B Ratio
            pb_div = ratios_section.find('div', text=lambda x: x and 'Book Value' in x)
            if pb_div:
                pb_value = pb_div.find_next('div').get_text(strip=True)
                try:
                    metrics['pb_ratio'] = float(pb_value.replace(',', ''))
                except ValueError:
                    metrics['pb_ratio'] = "N/A"
            
            # Dividend Yield
            div_div = ratios_section.find('div', text=lambda x: x and 'Dividend Yield' in x)
            if div_div:
                div_value = div_div.find_next('div').get_text(strip=True)
                try:
                    metrics['dividend_yield'] = float(div_value.replace('%', '').replace(',', ''))
                except ValueError:
                    metrics['dividend_yield'] = "N/A"
            
            # PEG Ratio
            peg_div = ratios_section.find('div', text=lambda x: x and 'PEG Ratio' in x)
            if peg_div:
                peg_value = peg_div.find_next('div').get_text(strip=True)
                try:
                    metrics['peg_ratio'] = float(peg_value.replace(',', ''))
                except ValueError:
                    metrics['peg_ratio'] = "N/A"
            
            # 50-Day MA & 200-Day MA (from "Price Information" section)
            price_section = soup.find('section', id='price-information')
            if price_section:
                ma_50_div = price_section.find('div', text=lambda x: x and '50-Day MA' in x)
                if ma_50_div:
                    ma_50_value = ma_50_div.find_next('div').get_text(strip=True)
                    try:
                        metrics['ma_50'] = float(ma_50_value.replace(',', ''))
                    except ValueError:
                        metrics['ma_50'] = "N/A"
                
                ma_200_div = price_section.find('div', text=lambda x: x and '200-Day MA' in x)
                if ma_200_div:
                    ma_200_value = ma_200_div.find_next('div').get_text(strip=True)
                    try:
                        metrics['ma_200'] = float(ma_200_value.replace(',', ''))
                    except ValueError:
                        metrics['ma_200'] = "N/A"
            
            return {
                'company_name': company_name,
                'current_price': current_price,
                'metrics': metrics
            }
            
        except Exception as e:
            return None

    with st.spinner(f"Fetching data for {symbol}..."):
        data = scrape_screener_consolidated(symbol)
        
        if not data:
            st.error("❌ Data not found. Try:")
            st.markdown("""
            - **Valid NSE symbols**: `RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `SBIN`
            - Avoid `.NS` suffix — just use `TCS`, not `TCS.NS`
            """)
            st.stop()

        # Display header
        st.subheader(f"{data['company_name']} • {symbol}.NS")
        st.metric("Current Price", f"₹{data['current_price']}" if data['current_price'] != "N/A" else "N/A")

        # Valuation metrics table
        st.subheader("Valuation Metrics (Latest)")
        metrics_list = [
            ("P/E Ratio", data['metrics'].get('pe_ratio', "N/A")),
            ("P/B Ratio", data['metrics'].get('pb_ratio', "N/A")),
            ("PEG Ratio", data['metrics'].get('peg_ratio', "N/A")),
            ("Dividend Yield", f"{data['metrics'].get('dividend_yield', 0):.2f}%" if isinstance(data['metrics'].get('dividend_yield'), (int, float)) else data['metrics'].get('dividend_yield', "N/A")),
            ("50-Day MA", data['metrics'].get('ma_50', "N/A")),
            ("200-Day MA", data['metrics'].get('ma_200', "N/A"))
        ]
        df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
        st.table(df)

        # Educational insights
        st.subheader("Educational Insights")
        pe = data['metrics'].get('pe_ratio', "N/A")
        pb = data['metrics'].get('pb_ratio', "N/A")
        peg = data['metrics'].get('peg_ratio', "N/A")

        insights = []
        if isinstance(pe, (int, float)) and pe < 15: insights.append("✅ P/E suggests undervaluation")
        elif isinstance(pe, (int, float)) and pe > 25: insights.append("⚠️ P/E suggests overvaluation")
        if isinstance(pb, (int, float)) and pb < 1.5: insights.append("✅ P/B suggests asset-backed value")
        elif isinstance(pb, (int, float)) and pb > 3: insights.append("⚠️ P/B suggests premium pricing")
        if isinstance(peg, (int, float)) and peg < 1: insights.append("✅ PEG < 1: growth may be undervalued")
        elif isinstance(peg, (int, float)) and peg > 2: insights.append("⚠️ PEG > 2: growth may be overpriced")

        for msg in insights or ["No strong valuation signals detected."]:
            st.info(msg)

# Ticker Guide
st.markdown("---")
st.subheader("How to Use (NSE Only)")
st.markdown("""
- **Enter NSE symbol only** → e.g., `RELIANCE`, `TCS`, `HDFCBANK`
- **No .NS suffix needed** — we auto-add it for Yahoo Finance
- **Not for BSE or global stocks** — this is NSE-only
""")

st.caption("Data: Screener.in (official) | Educational Use Only")
