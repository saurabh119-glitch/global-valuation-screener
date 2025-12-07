import streamlit as st
import pandas as pd
import time
import random
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="NSE Valuation Screener", page_icon="📈")
st.title("🇮🇳 NSE Stock Valuation Screener (Educational)")
st.caption("Compare metrics for NSE-listed stocks using NSE India + Screener.in + Moneycontrol. Not financial advice.")

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
    def get_nse_price(symbol):
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
                return "N/A"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract current price
            price_elem = soup.find('div', class_='last-price')
            if price_elem:
                return price_elem.get_text(strip=True).replace(',', '')
            
            return "N/A"
            
        except Exception as e:
            return "N/A"

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
            
            # PEG Ratio
            peg_div = ratios_section.find('div', text=lambda x: x and 'PEG Ratio' in x)
            if peg_div:
                peg_value = peg_div.find_next('div').get_text(strip=True)
                try:
                    metrics['peg_ratio'] = float(peg_value.replace(',', ''))
                except ValueError:
                    metrics['peg_ratio'] = "N/A"
            
            return {
                'company_name': company_name,
                'metrics': metrics
            }
            
        except Exception as e:
            return None

    @st.cache_data(ttl=3600)
    def scrape_moneycontrol(symbol):
        # Convert to Moneycontrol format (e.g., RELIANCE → reliance)
        moneycontrol_id = symbol.lower()
        url = f"https://www.moneycontrol.com/india/stockpricequote/{moneycontrol_id}/{moneycontrol_id}"
        
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
            session.get("https://www.moneycontrol.com", timeout=10)
            
            # Then fetch quote page
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key metrics from Moneycontrol
            metrics = {}
            
            # P/E Ratio
            pe_elem = soup.find('div', text=lambda x: x and 'P/E Ratio' in x)
            if pe_elem:
                pe_value = pe_elem.find_next('div').get_text(strip=True)
                try:
                    metrics['pe_ratio'] = float(pe_value.replace(',', ''))
                except ValueError:
                    metrics['pe_ratio'] = "N/A"
            
            # P/B Ratio
            pb_elem = soup.find('div', text=lambda x: x and 'P/B Ratio' in x)
            if pb_elem:
                pb_value = pb_elem.find_next('div').get_text(strip=True)
                try:
                    metrics['pb_ratio'] = float(pb_value.replace(',', ''))
                except ValueError:
                    metrics['pb_ratio'] = "N/A"
            
            # Dividend Yield
            div_elem = soup.find('div', text=lambda x: x and 'Dividend Yield' in x)
            if div_elem:
                div_value = div_elem.find_next('div').get_text(strip=True)
                try:
                    metrics['dividend_yield'] = float(div_value.replace('%', '').replace(',', ''))
                except ValueError:
                    metrics['dividend_yield'] = "N/A"
            
            # PEG Ratio
            peg_elem = soup.find('div', text=lambda x: x and 'PEG Ratio' in x)
            if peg_elem:
                peg_value = peg_elem.find_next('div').get_text(strip=True)
                try:
                    metrics['peg_ratio'] = float(peg_value.replace(',', ''))
                except ValueError:
                    metrics['peg_ratio'] = "N/A"
            
            return metrics
            
        except Exception as e:
            return None

    with st.spinner(f"Fetching data for {symbol}..."):
        # Get NSE price (real-time)
        nse_price = get_nse_price(symbol)
        
        # Get Screener data
        screener_data = scrape_screener_consolidated(symbol)
        
        # Get Moneycontrol data
        moneycontrol_data = scrape_moneycontrol(symbol)
        
        # Initialize final metrics
        final_metrics = {
            "P/E Ratio": "N/A",
            "P/B Ratio": "N/A",
            "PEG Ratio": "N/A",
            "Dividend Yield": "N/A",
            "50-Day MA": "N/A",
            "200-Day MA": "N/A"
        }

        # Priority: Screener.in > Moneycontrol > Fallback to "N/A"
        if screener_data:
            final_metrics["P/E Ratio"] = screener_data['metrics'].get('pe_ratio', "N/A")
            final_metrics["P/B Ratio"] = screener_data['metrics'].get('pb_ratio', "N/A")
            final_metrics["PEG Ratio"] = screener_data['metrics'].get('peg_ratio', "N/A")
            final_metrics["Dividend Yield"] = screener_data['metrics'].get('dividend_yield', "N/A")
            company_name = screener_data['company_name']
        elif moneycontrol_data:
            final_metrics["P/E Ratio"] = moneycontrol_data.get('pe_ratio', "N/A")
            final_metrics["P/B Ratio"] = moneycontrol_data.get('pb_ratio', "N/A")
            final_metrics["PEG Ratio"] = moneycontrol_data.get('peg_ratio', "N/A")
            final_metrics["Dividend Yield"] = moneycontrol_data.get('dividend_yield', "N/A")
            company_name = symbol
        else:
            company_name = symbol

        # Display header
        st.subheader(f"{company_name} • {symbol}.NS")
        st.metric("Current Price", f"₹{nse_price}" if nse_price != "N/A" else "N/A")

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

st.caption("Data: NSE India + Screener.in + Moneycontrol | Educational Use Only")
