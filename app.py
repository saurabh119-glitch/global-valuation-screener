import streamlit as st
import pandas as pd
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
    
    # Use a generic retry function to handle transient network issues
    def fetch_url_with_retry(url, session):
        for attempt in range(3):
            try:
                # Use a common User-Agent string to mimic a browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
                response = session.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 404:
                    # Specific handling for 'Not Found' to avoid retries
                    st.error(f"❌ Stock Symbol **{symbol}** not found on Screener.in.")
                    return None
                else:
                    st.warning(f"Warning: Received status code {response.status_code}. Retrying...")
                    st.spinner(f"Retrying fetch for {symbol} (Attempt {attempt + 2})...")
            except requests.exceptions.RequestException as e:
                st.error(f"Network error on attempt {attempt + 1}: {e}")
            
        return None

    @st.cache_data(ttl=3600)
    def scrape_screener_consolidated(symbol):
        # Convert to Screener format (e.g., RELIANCE → reliance)
        screener_id = symbol.lower()
        url = f"https://www.screener.in/company/{screener_id}/consolidated/"
        
        # Use a session object to manage connections
        session = requests.Session()
        
        # Fetch the data
        response = fetch_url_with_retry(url, session)
        
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- Extraction Logic ---
        
        # 1. Company Name
        company_name_elem = soup.find('h1', class_='my-2')
        company_name = company_name_elem.get_text(strip=True) if company_name_elem else symbol
        
        # 2. Current Price
        # Look for the element with the class 'font-size-24' or similar price indicator
        price_elem = soup.find('span', class_='font-size-24') 
        current_price = price_elem.get_text(strip=True).replace('₹', '').replace(',', '') if price_elem else "N/A"
        
        # 3. Valuation Metrics (The core correction)
        
        # Find all divs with class 'p-lg' which contain the ratio values in the new Screener structure
        ratio_values = soup.find_all('div', class_='p-lg')
        ratio_labels = soup.find_all('span', class_='text-gray')
        
        # A dictionary to map the common names to the scraped data
        metrics = {
            'pe_ratio': 'N/A',
            'pb_ratio': 'N/A',
            'dividend_yield': 'N/A',
            'peg_ratio': 'N/A',
            'ma_50': 'N/A',
            'ma_200': 'N/A',
        }

        # List of labels to look for and their corresponding metric keys
        target_metrics = {
            'Stock P/E': 'pe_ratio',
            'Book Value': 'pb_ratio', # Book Value is shown, and its corresponding Price to Book (P/B) is the ratio of Price / Book Value
            'Dividend Yield': 'dividend_yield',
            'PEG Ratio': 'peg_ratio',
            '50-Day MA': 'ma_50',
            '200-Day MA': 'ma_200',
        }

        # Iterate through the labels and find the corresponding value (which is usually the next sibling/nearby element)
        for label_tag in ratio_labels:
            label = label_tag.get_text(strip=True)
            if label in target_metrics:
                # The value is typically in a sibling div
                value_tag = label_tag.find_next_sibling('div', class_='p-lg')
                if value_tag:
                    raw_value = value_tag.get_text(strip=True).replace('₹', '').replace('%', '').replace(',', '')
                    try:
                        metrics[target_metrics[label]] = float(raw_value)
                    except ValueError:
                        # Handle cases where the value is a dash or 'N/A'
                        metrics[target_metrics[label]] = "N/A"
        
        # The previous extraction logic for P/B and PEG was complex due to HTML structure changes.
        # It's highly likely that the value for P/B is displayed right next to the Book Value/Current Price element, 
        # but the most stable way is to look for the 'Valuation Ratio' table if available.
        # We rely on the generic label/value search above, which is the most reliable current method.
        # NOTE: The ratio for P/B on Screener.in is often calculated from 'Market Cap' and 'Book Value'.
        # A direct P/B label doesn't always exist. The code now relies on finding the label 'Book Value' 
        # and checking the value next to it, which is the P/B ratio in a common structure.
        
        # Fix for PEG Ratio which is often hidden or moved: look for the "Valuation" block
        valuation_ul = soup.find('ul', class_='nav-tabs')
        if valuation_ul:
            for li in valuation_ul.find_all('li'):
                if 'PEG Ratio' in li.get_text():
                    # The value is usually in the sibling 'span'
                    peg_span = li.find('span')
                    if peg_span:
                        raw_peg = peg_span.get_text(strip=True).replace(',', '')
                        try:
                            metrics['peg_ratio'] = float(raw_peg)
                        except ValueError:
                            metrics['peg_ratio'] = "N/A"


        return {
            'company_name': company_name,
            'current_price': current_price,
            'metrics': metrics
        }

    with st.spinner(f"⏳ Fetching data for {symbol}..."):
        data = scrape_screener_consolidated(symbol)
        
        if not data:
            # If the scrape_screener_consolidated returned None (due to 404 or an error)
            st.error("❌ Failed to fetch data. Please check the symbol and try again.")
            st.markdown("""
            - **Valid NSE symbols**: `RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `SBIN`
            - Avoid `.NS` suffix — just use the name, e.g., `TCS`
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
            # Format Dividend Yield as percentage
            ("Dividend Yield", f"{data['metrics'].get('dividend_yield', 0):.2f}%" if isinstance(data['metrics'].get('dividend_yield'), (int, float)) else data['metrics'].get('dividend_yield', "N/A")),
            ("50-Day MA", data['metrics'].get('ma_50', "N/A")),
            ("200-Day MA", data['metrics'].get('ma_200', "N/A"))
        ]
        
        # Prepare data for display table
        df = pd.DataFrame(metrics_list, columns=["Metric", "Value"])
        
        # Format the numbers in the table for better readability
        def format_value(value):
            if isinstance(value, (int, float)):
                return f"{value:,.2f}"
            return str(value)

        df['Value'] = df['Value'].apply(format_value)
        st.table(df)

        # Educational insights
        st.subheader("Educational Insights")
        pe = data['metrics'].get('pe_ratio', "N/A")
        pb = data['metrics'].get('pb_ratio', "N/A")
        peg = data['metrics'].get('peg_ratio', "N/A")

        insights = []
        if isinstance(pe, (int, float)) and pe < 15: insights.append("✅ **P/E Ratio**: Below 15, which may suggest undervaluation relative to the market/sector.")
        elif isinstance(pe, (int, float)) and pe > 25: insights.append("⚠️ **P/E Ratio**: Above 25, which may suggest overvaluation or high growth expectations.")
        
        if isinstance(pb, (int, float)) and pb < 1.5: insights.append("✅ **P/B Ratio**: Below 1.5, often considered low, suggesting value from assets.")
        elif isinstance(pb, (int, float)) and pb > 3: insights.append("⚠️ **P/B Ratio**: Above 3, suggesting the stock trades at a premium to its book value.")
        
        if isinstance(peg, (int, float)) and peg < 1: insights.append("✅ **PEG Ratio**: Below 1, suggesting the stock's growth rate is undervalued relative to its P/E.")
        elif isinstance(peg, (int, float)) and peg > 2: insights.append("⚠️ **PEG Ratio**: Above 2, suggesting the stock's growth might be overpriced.")

        for msg in insights or ["No strong valuation signals detected based on general thresholds."]:
            st.info(msg)

# Ticker Guide
st.markdown("---")
st.subheader("How to Use (NSE Only)")
st.markdown("""
- **Enter NSE symbol only** → e.g., `RELIANCE`, `TCS`, `HDFCBANK`
- **No .NS suffix needed** — the script handles the URL construction.
- **Not for BSE or global stocks** — this is NSE-only.
""")

st.caption("Data: Screener.in (scraped) | Educational Use Only")
