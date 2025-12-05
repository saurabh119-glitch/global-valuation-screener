import streamlit as st
import yfinance as yf
import pandas as pd
import time
import random
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Global Valuation Screener", page_icon="📈")
st.title("🌍 Global Stock Valuation Screener (Educational)")
st.caption("Compare metrics for US, NSE, BSE stocks. Not financial advice.")

# Mandatory Disclaimer
st.warning("""
**Disclaimer**: This tool is for **educational purposes only**.  
It does **not** constitute investment advice.  
Trading involves high risk. Consult a **SEBI-registered advisor** before acting.
""")

# User input
ticker_input = st.text_input("Enter Stock Ticker (e.g., TCS, RELIANCE, AAPL)", "RELIANCE")

if ticker_input:
    # Clean input
    base_ticker = ticker_input.strip().upper()
    
    # Auto-append .NS for Indian tickers that don't have exchange suffix
    if not base_ticker.endswith(('.NS', '.BO', '.T', '.L')):
        candidates = [f"{base_ticker}.NS", f"{base_ticker}.BO"]
    elif base_ticker.endswith('.NS') or base_ticker.endswith('.BO'):
        candidates = [base_ticker]
    else:
        candidates = [base_ticker]

    @st.cache_data(ttl=3600)
    def fetch_yahoo_data(ticker, max_retries=2):
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                if info and 'symbol' in info:
                    hist = stock.history(period="1d")
                    price = hist['Close'].iloc[-1] if len(hist) > 0 else "N/A"
                    return info, price, ticker
            except Exception as e:
                if attempt == max_retries - 1:
                    return None, str(e), ticker
            time.sleep(1 + random.uniform(0, 0.5))
        return None, "Max retries exceeded", ticker

    @st.cache_data(ttl=3600)
    def scrape_screener(ticker):
        # Convert ticker to Screener format (e.g., RELIANCE.NS → reliance)
        if ticker.endswith('.NS'):
            screener_id = ticker[:-3].lower()  # RELIANCE.NS → reliance
        elif ticker.endswith('.BO'):
            screener_id = ticker[:-3].lower()  # INFY.BO → infy
        else:
            return None  # Not Indian stock

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
                metrics['pe_ratio'] = float(pe_text.replace(',', '')) if pe_text.replace(',', '').replace('.', '').isdigit() else "N/A"
            
            # P/B Ratio
            pb_elem = soup.find('li', text=lambda x: x and 'P/B Ratio' in x)
            if pb_elem:
                pb_text = pb_elem.find_next('span').get_text(strip=True)
                metrics['pb_ratio'] = float(pb_text.replace(',', '')) if pb_text.replace(',', '').replace('.', '').isdigit() else "N/A"
            
            # Dividend Yield
            div_elem = soup.find('li', text=lambda x: x and 'Dividend Yield' in x)
            if div_elem:
                div_text = div_elem.find_next('span').get_text(strip=True)
                metrics['dividend_yield'] = float(div_text.replace('%', '').replace(',', '')) if '%' in div_text else "N/A"
            
            # PEG Ratio (if available)
            peg_elem = soup.find('li', text=lambda x: x and 'PEG Ratio' in x)
            if peg_elem:
                peg_text = peg_elem.find_next('span').get_text(strip=True)
                metrics['peg_ratio'] = float(peg_text.replace(',', '')) if peg_text.replace(',', '').replace('.', '').isdigit() else "N/A"
            
            return metrics
            
        except Exception as e:
            return None

    # Fetch Yahoo data first
    info, current_price, used_ticker = None, "N/A", None
    for ticker in candidates:
        with st.spinner(f"Fetching {ticker}..."):
            info, current_price, used_ticker = fetch_yahoo_data(ticker)
            if info is not None:
                break

    if info is None:
        st.error("❌ No data found. Try:")
        st.markdown("""
        - **NSE**: `RELIANCE`, `TCS`, `HDFCBANK`  
        - **BSE**: `INFY`, `SBIN`  
        - **US**: `AAPL`, `MSFT`
        """)
        st.stop()

    # Get company name and exchange
    company_name = info.get("longName", used_ticker)
    exchange = info.get("exchange", "N/A")

    # Display header
    st.subheader(f"{company_name} • {used_ticker}")
    st.metric("Current Price", f"₹{current_price:.2f}" if isinstance(current_price, float) else current_price)

    # Initialize metrics
    final_metrics = {
        "P/E Ratio": info.get("trailingPE", "N/A"),
        "P/B Ratio": info.get("priceToBook", "N/A"),
        "PEG Ratio": info.get("pegRatio", "N/A"),
        "Dividend Yield": info.get("dividendYield", 0)*100 if info.get("dividendYield") else "N/A",
        "50-Day MA": info.get("fiftyDayAverage", "N/A"),
        "200-Day MA": info.get("twoHundredDayAverage", "N/A")
    }

    # If Indian stock, try to scrape Screener.in for better metrics
    if used_ticker.endswith(('.NS', '.BO')):
        st.info("🔍 Fetching accurate metrics from Screener.in...")
        screener_data = scrape_screener(used_ticker)
        
        if screener_data:
            # Update metrics if Screener data is valid
            if screener_data.get('pe_ratio') != "N/A":
                final_metrics["P/E Ratio"] = screener_data['pe_ratio']
            if screener_data.get('pb_ratio') != "N/A":
                final_metrics["P/B Ratio"] = screener_data['pb_ratio']
            if screener_data.get('dividend_yield') != "N/A":
                final_metrics["Dividend Yield"] = screener_data['dividend_yield']
            if screener_data.get('peg_ratio') != "N/A":
                final_metrics["PEG Ratio"] = screener_data['peg_ratio']

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
st.subheader("How to Use (India-Friendly)")
st.markdown("""
- **Just type the stock name** → we auto-add `.NS` or `.BO`  
  → e.g., `RELIANCE` → tries `RELIANCE.NS` then `RELIANCE.BO`
- **Or specify exchange**:  
  - NSE: `TCS.NS`  
  - BSE: `INFY.BO`
- **Global stocks**: `AAPL` (US), `7203.T` (Japan)
""")

st.caption("Data: Yahoo Finance + Screener.in (for Indian stocks) | Educational Use Only")
