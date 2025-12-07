import streamlit as st
import yfinance as yf
import pandas as pd
import time
import random
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="NSE Valuation Screener", page_icon="📈")
st.title("🇮🇳 NSE Stock Valuation Screener (Educational)")
st.caption("Compare metrics for NSE-listed stocks using Screener.in + Yahoo Finance. Not financial advice.")

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
    def get_yahoo_data(symbol):
        try:
            stock = yf.Ticker(symbol + ".NS")  # Add .NS for Indian stocks
            info = stock.info
            hist = stock.history(period="1d")
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else "N/A"
            return info, current_price
        except Exception as e:
            return None, f"Error: {str(e)}"

    @st.cache_data(ttl=3600)
    def scrape_screener(symbol):
        # Convert to Screener format (e.g., RELIANCE → reliance)
        screener_id = symbol.lower()
        url = f"https://www.screener.in/company/{screener_id}/"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key metrics from Screener
            metrics = {}
            
            # P/E Ratio
            pe_elem = soup.find('li', text=lambda x: x and 'P/E Ratio' in x)
            if pe_elem:
                pe_text = pe_elem.find_next('span').get_text(strip=True)
                try:
                    metrics['pe_ratio'] = float(pe_text.replace(',', ''))
                except ValueError:
                    metrics['pe_ratio'] = "N/A"
            
            # P/B Ratio
            pb_elem = soup.find('li', text=lambda x: x and 'P/B Ratio' in x)
            if pb_elem:
                pb_text = pb_elem.find_next('span').get_text(strip=True)
                try:
                    metrics['pb_ratio'] = float(pb_text.replace(',', ''))
                except ValueError:
                    metrics['pb_ratio'] = "N/A"
            
            # Dividend Yield
            div_elem = soup.find('li', text=lambda x: x and 'Dividend Yield' in x)
            if div_elem:
                div_text = div_elem.find_next('span').get_text(strip=True)
                try:
                    metrics['dividend_yield'] = float(div_text.replace('%', '').replace(',', ''))
                except ValueError:
                    metrics['dividend_yield'] = "N/A"
            
            # PEG Ratio (from Screener.in's consolidated page)
            peg_div = soup.find('div', text=lambda x: x and 'PEG Ratio' in x)
            if peg_div:
                peg_value = peg_div.find_next('div').get_text(strip=True)
                try:
                    metrics['peg_ratio'] = float(peg_value.replace(',', ''))
                except ValueError:
                    metrics['peg_ratio'] = "N/A"
            
            return metrics
            
        except Exception as e:
            return None

    with st.spinner(f"Fetching data for {symbol}..."):
        # Get Yahoo data
        info, current_price = get_yahoo_data(symbol)
        if info is None:
            st.error(current_price)
            st.info("Try a different ticker like `TCS`, `RELIANCE`, or `HDFCBANK`.")
            st.stop()

        # Get Screener data
        screener_data = scrape_screener(symbol)
        
        # Initialize final metrics
        final_metrics = {
            "P/E Ratio": info.get("trailingPE", "N/A"),
            "P/B Ratio": info.get("priceToBook", "N/A"),
            "PEG Ratio": info.get("pegRatio", "N/A"),
            "Dividend Yield": info.get("dividendYield", 0)*100 if info.get("dividendYield") else "N/A",
            "50-Day MA": info.get("fiftyDayAverage", "N/A"),
            "200-Day MA": info.get("twoHundredDayAverage", "N/A")
        }

        # If Screener data is available, update metrics
        if screener_data:
            if screener_data.get('pe_ratio') != "N/A":
                final_metrics["P/E Ratio"] = screener_data['pe_ratio']
            if screener_data.get('pb_ratio') != "N/A":
                final_metrics["P/B Ratio"] = screener_data['pb_ratio']
            if screener_data.get('dividend_yield') != "N/A":
                final_metrics["Dividend Yield"] = screener_data['dividend_yield']
            if screener_data.get('peg_ratio') != "N/A":
                final_metrics["PEG Ratio"] = screener_data['peg_ratio']

        # Display header
        company_name = info.get("longName", symbol)
        st.subheader(f"{company_name} • {symbol}.NS")
        st.metric("Current Price", f"₹{current_price:.2f}" if isinstance(current_price, float) else current_price)

        # Valuation metrics table
        st.subheader("Valuation Metrics (Latest)")
        metrics_list = [
            ("P/E Ratio", final_metrics["P/E Ratio"]),
            ("P/B Ratio", final_metrics["P/B Ratio"]),
            ("PEG Ratio", final_metrics["PEG Ratio"]),
            ("Dividend Yield", f"{final_metrics['Dividend Yield']:.2f}%" if isinstance(final_metrics['Dividend Yield'], (int, float)) else final_metrics['Dividend Yield']),
            ("50-Day MA", final_metrics["50-Day MA"]),
            ("200-Day MA", final_metrics["200-Day MA"])
        ]
        df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
        st.table(df)

        # Educational insights
        st.subheader("Educational Insights")
        pe = final_metrics["P/E Ratio"]
        pb = final_metrics["P/B Ratio"]
        peg = final_metrics["PEG Ratio"]

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

st.caption("Data: Screener.in + Yahoo Finance | Educational Use Only")
