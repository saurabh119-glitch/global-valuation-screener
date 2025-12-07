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
            
            return {
                'company_name': company_name,
                'metrics': metrics
            }
            
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
        screener_data = scrape_screener_consolidated(symbol)
        
        # Initialize final metrics
        final_metrics = {
            "P/E Ratio": info.get("trailingPE", "N/A"),
            "P/B Ratio": info.get("priceToBook", "N/A"),
            "Dividend Yield": info.get("dividendYield", 0)*100 if info.get("dividendYield") else "N/A",
            "50-Day MA": info.get("fiftyDayAverage", "N/A"),
            "200-Day MA": info.get("twoHundredDayAverage", "N/A")
        }

        # If Screener data is available, update metrics safely
        if screener_data and 'metrics' in screener_data:
            final_metrics["P/E Ratio"] = screener_data['metrics'].get('pe_ratio', final_metrics["P/E Ratio"])
            final_metrics["P/B Ratio"] = screener_data['metrics'].get('pb_ratio', final_metrics["P/B Ratio"])
            final_metrics["Dividend Yield"] = screener_data['metrics'].get('dividend_yield', final_metrics["Dividend Yield"])

        # Display header
        company_name = info.get("longName", symbol)
        st.subheader(f"{company_name} • {symbol}.NS")
        st.metric("Current Price", f"₹{current_price:.2f}" if isinstance(current_price, float) else current_price)

        # Valuation metrics table
        st.subheader("Valuation Metrics (Latest)")
        metrics_list = [
            ("P/E Ratio", final_metrics["P/E Ratio"]),
            ("P/B Ratio", final_metrics["P/B Ratio"]),
            ("Dividend Yield", f"{final_metrics['Dividend Yield']:.2f}%" if isinstance(final_metrics['Dividend Yield'], (int, float)) else final_metrics['Dividend Yield']),
            ("50-Day MA", final_metrics["50-Day MA"]),
            ("200-Day MA", final_metrics["200-Day MA"])
        ]
        df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
        st.table(df)

        # No Educational Insights — just show the data
        # st.subheader("Educational Insights")
        # ... removed per your request

# Ticker Guide
st.markdown("---")
st.subheader("How to Use (NSE Only)")
st.markdown("""
- **Enter NSE symbol only** → e.g., `RELIANCE`, `TCS`, `HDFCBANK`
- **No .NS suffix needed** — we auto-add it for Yahoo Finance
- **Not for BSE or global stocks** — this is NSE-only
""")

st.caption("Data: Screener.in + Yahoo Finance | Educational Use Only")
