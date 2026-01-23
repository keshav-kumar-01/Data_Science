import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ta
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime, timedelta

from algorithms import * # Load Analysis Logic
from rate_limiter import rate_limiter  # Import rate limiter

# ==========================================
# ⚙️ CONFIGURATION & DATA ENGINE
# ==========================================
st.set_page_config(page_title="In-House Bloomberg Terminal", layout="wide")

# Sidebar for Ticker Input
st.sidebar.header("🕹️ Command Center")

# Predefined Groups - Comprehensive Lists
GLOBAL_MAP = {
    "India (NIFTY 50)": [
        "^NSEI", "^BSESN", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", 
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "KOTAKBANK.NS", 
        "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", 
        "ULTRACEMCO.NS", "NESTLEIND.NS", "BAJFINANCE.NS", "HCLTECH.NS", "WIPRO.NS", "ONGC.NS",
        "NTPC.NS", "POWERGRID.NS", "M&M.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "ADANIENT.NS",
        "COALINDIA.NS", "JSWSTEEL.NS", "INDUSINDBK.NS", "BAJAJFINSV.NS", "TECHM.NS"
    ],
    "US (NYSE & NASDAQ)": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK-B", "JPM", "JNJ", 
        "V", "PG", "UNH", "MA", "HD", "DIS", "PYPL", "NFLX", "ADBE", "CRM", "INTC", 
        "CSCO", "PFE", "KO", "PEP", "NKE", "MRK", "T", "VZ", "WMT", "BAC", "XOM", 
        "CVX", "ABBV", "TMO", "COST", "AVGO", "ORCL", "ACN", "MCD", "ABT", "DHR", 
        "TXN", "NEE", "LLY", "MDT", "UNP", "LOW", "HON", "QCOM"
    ],
    "Commodities & FX": ["GC=F", "CL=F", "EURUSD=X", "USDINR=X", "BTC-USD", "SI=F", "NG=F"],
    "EU (London & Euronext)": [
        "^FTSE", "^FCHI", "^GDAXI", "SHEL.L", "AZN.L", "HSBA.L", "BP.L", "GSK.L", "DGE.L",
        "ULVR.L", "RIO.L", "NG.L", "BARC.L", "LLOY.L", "VOD.L", "MC.PA", "OR.PA", "SAN.PA",
        "AI.PA", "BN.PA", "SU.PA", "ASML.AS", "INGA.AS", "PHIA.AS", "SAP.DE", "SIE.DE",
        "ALV.DE", "DTE.DE", "VOW3.DE", "BAS.DE"
    ],
    "Japan (Tokyo)": [
        "^N225", "7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "8035.T", "4502.T",
        "9433.T", "6902.T", "6501.T", "6954.T", "6981.T", "7267.T", "7974.T", "4063.T",
        "4568.T", "6098.T", "8001.T", "8058.T"
    ],
    "China (Shanghai & Shenzhen)": [
        "000001.SS", "600519.SS", "601398.SS", "601939.SS", "601857.SS", "601288.SS",
        "600036.SS", "600276.SS", "600887.SS", "601318.SS", "000858.SZ", "000333.SZ",
        "002594.SZ", "300750.SZ", "002415.SZ", "000002.SZ"
    ],
    "Hong Kong": [
        "^HSI", "0700.HK", "1299.HK", "9988.HK", "3690.HK", "0005.HK", "0939.HK", 
        "2318.HK", "0388.HK", "1398.HK", "2628.HK", "0941.HK", "1810.HK", "2020.HK",
        "0883.HK", "1113.HK", "0016.HK", "0002.HK", "0011.HK", "0001.HK"
    ],
    "Asian Markets": ["^N225", "^HSI", "^STI", "^KLSE", "^JKSE"]
}

# Flatten all tickers for dropdown
ALL_TICKERS = []
for group_tickers in GLOBAL_MAP.values():
    ALL_TICKERS.extend(group_tickers)
ALL_TICKERS = sorted(list(set(ALL_TICKERS)))

market_select = st.sidebar.multiselect("Select Market Groups", list(GLOBAL_MAP.keys()), default=["India (NIFTY 50)"])
custom_tickers = st.sidebar.text_input("Add Custom Tickers (comma separated)", "")

# Aggregate Tickers
tickers = []
for m in market_select:
    tickers.extend(GLOBAL_MAP[m])

if custom_tickers:
    tickers.extend([t.strip().upper() for t in custom_tickers.split(',') if t])

# Filter out index tickers (starting with ^) from main portfolio view
tickers = sorted(list(set(tickers)))
stock_tickers = [t for t in tickers if not t.startswith('^')]  # Stocks only, no indices

# Rate limit warning
if len(tickers) > 15:
    st.sidebar.warning("⚠️ Large ticker list may take 3-5 minutes to load")
    
benchmark_ticker = "^NSEI"  # Use NIFTY as default benchmark

start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

# ==========================================
# 🔄 INCREMENTAL DATA ENGINE (Streaming Load)
# ==========================================

# Initialize Session State
if 'prices' not in st.session_state:
    st.session_state.prices = pd.DataFrame()
if 'market_prices' not in st.session_state:
    st.session_state.market_prices = pd.Series(dtype=float)
if 'last_config' not in st.session_state:
    st.session_state.last_config = ""
if 'failed_tickers' not in st.session_state:
    st.session_state.failed_tickers = set()

# Detect Config Changes (tickers, dates) and reset if needed
current_config = f"{','.join(tickers)}_{start_date}_{end_date}_{benchmark_ticker}"
if st.session_state.last_config != current_config:
    st.session_state.prices = pd.DataFrame()
    st.session_state.market_prices = pd.Series(dtype=float)
    st.session_state.failed_tickers = set()
    st.session_state.last_config = current_config

# Helper to load data in a traditional way (for Global Markets)
@st.cache_data(ttl=3600)
def load_data(tickers_list, start, end):
    return rate_limiter.download_in_batches(tickers_list, start, end)

# Helper to load data one-by-one (Incremental Loader)
def fetch_next_missing():
    # Only background load if not paused
    if st.session_state.get('paused', False):
        return

    # 1. Check Benchmark first
    if st.session_state.market_prices.empty:
        with st.sidebar.status(f"📡 Loading Benchmark {benchmark_ticker}..."):
            data = rate_limiter.download_with_retry([benchmark_ticker], start_date, end_date)
            if data is not None and not data.empty:
                prices_series = data.xs('Close', level='Price', axis=1) if 'Price' in data.columns.names else data['Close']
                st.session_state.market_prices = prices_series.squeeze()
                st.rerun()
            else:
                st.session_state.failed_tickers.add(benchmark_ticker)
                st.rerun()

    # 2. Check Stocks
    missing = [t for t in tickers if t not in st.session_state.prices.columns and t not in st.session_state.failed_tickers and t != benchmark_ticker]
    
    if missing:
        t = missing[0]
        with st.sidebar.status(f"🛰️ Loading {t}..."):
            data = rate_limiter.download_single_ticker(t, start_date, end_date)
            if data is not None and not data.empty:
                # Use a copy to avoid mutation issues
                df = st.session_state.prices.copy()
                if df.empty:
                    st.session_state.prices = pd.DataFrame({t: data})
                else:
                    st.session_state.prices[t] = data
                st.rerun()
            else:
                st.session_state.failed_tickers.add(t)
                st.rerun()

# Sidebar: Controls
st.sidebar.divider()
if st.sidebar.button("⏸️ Pause Loading" if not st.session_state.get('paused', False) else "▶️ Resume Loading"):
    st.session_state.paused = not st.session_state.get('paused', False)
    st.rerun()

# Run the fetcher
fetch_next_missing()

# Use state-based data
prices = st.session_state.prices
market_prices = st.session_state.market_prices

# Handle empty state for the rest of the app
if prices.empty:
    st.warning("📥 Terminal initialized. Loading market data ticker-by-ticker...")
    st.info("Check the sidebar for progress. Charts will appear as soon as the first ticker arrives.")
    # Show a progress bar for the total selection
    total = len(tickers)
    loaded = len(prices.columns)
    st.progress(loaded/total if total > 0 else 0)
    st.stop()

# Sidebar display of loaded/failed
st.sidebar.divider()
st.sidebar.caption(f"📈 Loaded: {len(prices.columns)} | ❌ Failed: {len(st.session_state.failed_tickers)}")
if len(st.session_state.failed_tickers) > 0:
    with st.sidebar.expander("View Failed Tickers"):
        st.write(list(st.session_state.failed_tickers))


# ==========================================
# 📊 PHASE 1: ADVANCED ALGORITHMS (The Engine)
# ==========================================

# Logic imported from algorithms.py

# ==========================================
# 🧠 PHASE 2: ML & DEEP LEARNING (The Predictor)
# ==========================================

# Logic imported from algorithms.py

# ==========================================
# 🖥️ PHASE 3: THE TERMINAL UI (Streamlit)
# ==========================================

st.title("📊 In-House Financial Terminal")

# Simple rate limit info
if len(tickers) > 15:
    st.info("ℹ️ Loading multiple tickers may take 2-3 minutes. Data is cached for 1 hour after first load.")

st.markdown("---")

# --- MAIN NAVIGATION ---
tab_port, tab_analysis, tab_global, tab_eco, tab_map, tab_social, tab_opt, tab_ai = st.tabs([
    "📂 My Portfolio", 
    "📊 Analysis (FA/DES)", 
    "🌍 Global Markets", 
    "📉 Economics (ECO)",
    "🗺️ Terminal Map",
    "☕ Social (POSH/IB)",
    "⚖️ Optimization", 
    "🤖 AI Forecast"
])

with tab_global:
    st.subheader("🌍 Global Market Explorer")
    region = st.selectbox("Select Region / Exchange", [
        "India (NIFTY 50)", "US (NYSE & NASDAQ)", "EU (London & Euronext)", 
        "Japan (Tokyo)", "China (Shanghai & Shenzhen)", "Hong Kong"
    ])
    
    # Define Ticker Groups
    ticker_map = {
        "India (NIFTY 50)": ["^NSEI", "^BSESN", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS"],
        "US (NYSE & NASDAQ)": ["^GSPC", "^IXIC", "^DJI", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK-B", "JPM"],
        "EU (London & Euronext)": ["^FTSE", "^FCHI", "^GDAXI", "SHEL.L", "AZN.L", "MC.PA", "ASML.AS", "SAP.DE", "OR.PA", "HSBA.L"],
        "Japan (Tokyo)": ["^N225", "7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "8035.T", "4502.T"],
        "China (Shanghai & Shenzhen)": ["000001.SS", "399001.SZ", "600519.SS", "601398.SS", "601939.SS", "601857.SS", "601288.SS", "000858.SZ"],
        "Hong Kong": ["^HSI", "0700.HK", "1299.HK", "9988.HK", "3690.HK", "0005.HK", "0939.HK", "2318.HK"]
    }
    
    selected_region_tickers = ticker_map[region]
    
    with st.spinner(f"Fetching {region} data..."):
        try:
            regional_data = load_data(selected_region_tickers, start_date, end_date)
            
            if regional_data.empty or len(regional_data) == 0:
                st.error(f"No data available for {region}. Try selecting a different date range or region.")
            else:
                # Regional Performance Chart
                fig_global = go.Figure()
                # Normalize to 100 for comparison - handle first row safely
                first_row = regional_data.iloc[0]
                # Replace zeros to avoid division errors
                first_row = first_row.replace(0, 1)
                normalized_data = (regional_data / first_row) * 100
                
                for t in normalized_data.columns:
                    fig_global.add_trace(go.Scatter(x=normalized_data.index, y=normalized_data[t], mode='lines', name=t))
                
                fig_global.update_layout(height=600, template="plotly_dark", title=f"{region} Performance (Base 100)", yaxis_title="Normalized Price")
                st.plotly_chart(fig_global, width='stretch')
                
                # Heatmap of correlation within the region
                st.subheader(f"{region} Correlation Matrix")
                reg_corr = regional_data.pct_change().corr()
                fig_reg_corr = go.Figure(data=go.Heatmap(
                    z=reg_corr.values,
                    x=reg_corr.columns,
                    y=reg_corr.columns,
                    colorscale='RdBu', zmin=-1, zmax=1))
                st.plotly_chart(fig_reg_corr, width='stretch')
            
        except Exception as e:
            st.error(f"Error loading {region} data: {e}")

with tab_analysis:
    st.subheader("🔍 Deep Asset Analysis")
    target_asset = st.selectbox("Select Asset to Inspect", tickers, key="analysis_asset")
    
    try:
        ticker_obj = yf.Ticker(target_asset)
        info = ticker_obj.info
        
        col_a1, col_a2 = st.columns([2, 1])
        
        with col_a1:
            st.markdown(f"### DES: {info.get('longName', target_asset)}")
            st.write(info.get('longBusinessSummary', "No description available."))
            
            # Financial Data (FA)
            st.markdown("#### FA: Key Financials")
            fa_data = {
                "Metric": ["P/E Ratio", "Forward P/E", "Dividend Yield", "Market Cap", "Debt to Equity", "Return on Equity", "Beta"],
                "Value": [
                    str(info.get('trailingPE', 'N/A')),
                    str(info.get('forwardPE', 'N/A')),
                    f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else 'N/A',
                    f"${info.get('marketCap', 0):,}",
                    str(info.get('debtToEquity', 'N/A')),
                    f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else 'N/A',
                    str(info.get('beta', 'N/A'))
                ]
            }
            st.table(pd.DataFrame(fa_data))

        with col_a2:
            # Analyst Recommendations (ANR)
            st.markdown("#### ANR: Analyst Sentiment")
            try:
                recs = ticker_obj.recommendations
                if recs is not None and not recs.empty:
                    st.dataframe(recs.tail(5))
                else:
                    st.write("No recent analyst data.")
            except:
                st.write("Could not fetch analyst ratings.")
                
            # ESG Data
            st.markdown("#### ESG: Sustainability Score")
            st.write(f"Total ESG Risk: {info.get('totalEsg', 'N/A')}")
            st.write(f"Environment Risk: {info.get('environmentScore', 'N/A')}")
            st.write(f"Social Risk: {info.get('socialScore', 'N/A')}")
            st.progress(min(max(info.get('totalEsg', 50)/100, 0.0), 1.0) if isinstance(info.get('totalEsg'), (int, float)) else 0.5)

            # SPLC: Supply Chain
            st.markdown("#### SPLC: Supply Chain Analysis (Mocked)")
            splc_data = pd.DataFrame({
                "Entity": ["Primary Supplier A", "Logistics Partner B", "Key Customer C", "Competitor X"],
                "Relationship": ["Supplier", "Service", "Customer", "Competition"],
                "Exposure": ["High", "Medium", "Critical", "N/A"]
            })
            st.dataframe(splc_data)
    except Exception as e:
        st.error(f"⚠️ Rate Limited or API Error: {str(e)[:100]}... Please wait a moment and refresh.")

with tab_eco:
    st.subheader("📉 World Economic Indicators (ECO)")
    eco_indices = {
        "US 10Y Yield": "^TNX",
        "Volatility Index (VIX)": "^VIX",
        "Gold Spot": "GC=F",
        "WTI Crude Oil": "CL=F",
        "Dollar Index (DXY)": "DX-Y.NYB",
        "EUR/USD": "EURUSD=X"
    }
    
    eco_cols = st.columns(3)
    for i, (name, t) in enumerate(eco_indices.items()):
        with eco_cols[i % 3]:
            try:
                eco_data = yf.download(t, period="5d")
                curr = eco_data['Close'].iloc[-1].iloc[0] if isinstance(eco_data['Close'].iloc[-1], pd.Series) else eco_data['Close'].iloc[-1]
                prev = eco_data['Close'].iloc[-2].iloc[0] if isinstance(eco_data['Close'].iloc[-2], pd.Series) else eco_data['Close'].iloc[-2]
                change = ((curr - prev)/prev)*100
                st.metric(name, f"{curr:.2f}", f"{change:.2f}%")
            except:
                st.metric(name, "N/A", "0%")
with tab_port:
    col_opt, col_graph = st.columns([1, 4])

with tab_map:
    st.subheader("🗺️ Terminal Real-Time Map (MAP)")
    st.write("Visualizing Global Shipping and Flight Proxies (Simulated)")
    
    # Generate mock locations for demonstrations
    map_data = pd.DataFrame({
        'lat': [40.7128, 51.5074, 35.6895, 22.3193, 19.0760, 48.8566],
        'lon': [-74.0060, -0.1278, 139.6917, 114.1694, 72.8777, 2.3522],
        'type': ['Port', 'Airport', 'Oil Tanker', 'Cargo Ship', 'Port', 'Airport'],
        'status': ['Active', 'Delayed', 'On Route', 'Stationary', 'Active', 'Active']
    })
    
    import plotly.express as px
    fig_map = px.scatter_mapbox(map_data, lat="lat", lon="lon", color="type", 
                                hover_name="status", zoom=1, height=600)
    fig_map.update_layout(mapbox_style="carto-darkmatter")
    st.plotly_chart(fig_map, use_container_width=True)

with tab_social:
    st.subheader("☕ Bloomberg Lifestyle & Networking")
    
    social_col1, social_col2 = st.columns(2)
    
    with social_col1:
        st.markdown("### POSH: Luxury Classifieds")
        posh_items = {
            "Item": ["2023 Riva 76' Bahamas", "Rolex Daytona (Panda)", "Hamptons Oceanfront Estate", "Private Jet - G650ER"],
            "Price": ["$3.2M", "$42,000", "$18.5M", "$65M"],
            "Location": ["Monaco", "Hong Kong", "NY, USA", "Global"]
        }
        st.table(pd.DataFrame(posh_items))
        
        st.markdown("### DINE: Elite Dining")
        st.write("🍴 **Le Bernardin (NY)** - 3 Michelin Stars. *Highly Recommended*.")
        st.write("🍴 **Gaggan Anand (Bangkok)** - Progressive Indian.")

with tab_port:
    st.subheader("📂 My Portfolio Overview")
    
    # Ticker Selection for Charts
    loaded_tickers = list(prices.columns)
    pending_tickers = [t for t in stock_tickers if t not in loaded_tickers and t not in st.session_state.failed_tickers]
    
    selected_tickers = st.multiselect(
        "Select Stocks to Display", 
        options=stock_tickers,
        default=loaded_tickers[:5],
        key="portfolio_ticker_select",
        help=f"Loaded: {len(loaded_tickers)} | Pending: {len(pending_tickers)} | Failed: {len(st.session_state.failed_tickers)}"
    )
    
    if pending_tickers and not st.session_state.get('paused', False):
        st.caption(f"⏳ Background loading: {len(pending_tickers)} tickers remaining...")
    
    if not selected_tickers:
        st.warning("⚠️ Please select at least one ticker to display.")
    else:
        col_opt, col_graph = st.columns([1, 4])
        
        with col_opt:
            st.subheader("Technical Indicators")
            show_rsi = st.checkbox("Show RSI")
            show_bb = st.checkbox("Show Bollinger Bands")
            show_macd = st.checkbox("Show MACD")
            show_candle = st.checkbox("Show Candlesticks")
            
            st.divider()
            st.subheader("BQL: Excel Integration")
            if st.download_button(
                label="Download Data as CSV",
                data=prices.to_csv(),
                file_name="bloomberg_data.csv",
                mime="text/csv",
            ):
                st.success("Exported to Excel compatible format!")

        with col_graph:
            st.subheader("Price History & Technicals")
            
            # Main Chart
            fig = go.Figure()
            
            # Add basic price traces - only for selected tickers
            for t in selected_tickers:
                if t not in prices.columns:
                    continue
                
                if show_candle:
                    # Need OHLC data for candles (download separately as prices only contains 'Close')
                    try:
                        candle_data = yf.download(t, start=start_date, end=end_date, progress=False)
                        if not candle_data.empty:
                            fig.add_trace(go.Candlestick(
                                x=candle_data.index,
                                open=candle_data['Open'],
                                high=candle_data['High'],
                                low=candle_data['Low'],
                                close=candle_data['Close'],
                                name=f"{t} (OHLC)"
                            ))
                    except:
                        fig.add_trace(go.Scatter(x=prices.index, y=prices[t], mode='lines', name=t))
                else:
                    fig.add_trace(go.Scatter(x=prices.index, y=prices[t], mode='lines', name=t))
                
                # Technical Indicators per ticker
                if show_bb:
                    indicator_bb = BollingerBands(close=prices[t], window=20, window_dev=2)
                    bb_upper = indicator_bb.bollinger_hband()
                    bb_lower = indicator_bb.bollinger_lband()
                    
                    if bb_upper is not None and bb_lower is not None:
                         fig.add_trace(go.Scatter(x=bb_upper.index, y=bb_upper, mode='lines', line=dict(width=1, dash='dot'), name=f"{t} Upper BB"))
                         fig.add_trace(go.Scatter(x=bb_lower.index, y=bb_lower, mode='lines', line=dict(width=1, dash='dot'), name=f"{t} Lower BB"))
        
        fig.update_layout(height=600, template="plotly_dark", title="Asset Prices")
        st.plotly_chart(fig, use_container_width=True)
        
        # Secondary Charts (RSI/MACD)
        
        if show_rsi:
            rsi_ticker = st.selectbox("Select Ticker for RSI", prices.columns, key="rsi_select")
            indicator_rsi = RSIIndicator(close=prices[rsi_ticker], window=14)
            rsi = indicator_rsi.rsi()
            fig_rsi = go.Figure(go.Scatter(x=rsi.index, y=rsi, name="RSI"))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            fig_rsi.update_layout(height=350, template="plotly_dark", title=f"RSI ({rsi_ticker})")
            st.plotly_chart(fig_rsi, use_container_width=True)
            
        if show_macd:
            macd_ticker = st.selectbox("Select Ticker for MACD", prices.columns, key="macd_select")
            indicator_macd = MACD(close=prices[macd_ticker], window_slow=26, window_fast=12, window_sign=9)
            macd_line = indicator_macd.macd()
            macd_sig = indicator_macd.macd_signal()
            macd_hist = indicator_macd.macd_diff()
            
            if macd_line is not None:
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(x=macd_line.index, y=macd_line, name="MACD"))
                fig_macd.add_trace(go.Scatter(x=macd_sig.index, y=macd_sig, name="Signal"))
                fig_macd.add_trace(go.Bar(x=macd_hist.index, y=macd_hist, name="Hist"))
                fig_macd.update_layout(height=350, template="plotly_dark", title=f"MACD ({macd_ticker})")
                st.plotly_chart(fig_macd, use_container_width=True)

    st.subheader("Asset Correlation")
    corr = prices.pct_change().corr()
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale='Viridis'))
    st.plotly_chart(fig_corr)

# --- TAB: Optimization ---
with tab_opt:
    st.markdown("""
    ### 🛡️ Portfolio Optimization & Risk Analysis
    Configure and optimize your asset allocation using industry-standard models.
    
    *   **Black-Litterman Model**: An advanced approach that combines market equilibrium (prior) with your own unique 'views' (predictions) to generate diversified weights.
    *   **Hierarchical Risk Parity (HRP)**: A modern ML-based optimization that clusters assets by correlation, ensuring your portfolio is resilient even when markets shift together.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Black-Litterman Allocation")
        
        with st.expander("Adjust Market Views"):
            st.write("Input absolute views (e.g. AAPL will return 10%)")
            view_ticker = st.selectbox("Ticker", prices.columns)
            # ... existing view code ...
            view_return = st.number_input("Expected Return (%)", min_value=-100.0, max_value=1000.0, value=10.0)
            view_conf = st.slider("Confidence", 0.0, 1.0, 0.5) 
        
        if st.button("Run Black-Litterman"):
            try:
                # Construct view dict
                view_dict = {view_ticker: view_return / 100.0}
                st.info(f"Using View: {view_dict}")
                
                bl_weights = run_black_litterman(prices, market_prices, view_dict=view_dict)
                if bl_weights:
                    st.write(bl_weights)
                    st.bar_chart(pd.Series(bl_weights))
                else:
                    st.warning("No weights returned. Check inputs.")
            except Exception as e:
                st.warning(f"Optimization failed: {e}")

    with col2:
        st.subheader("Hierarchical Risk Parity (HRP)")
        st.write("Groups assets by correlation distance to minimize risk.")
        if st.button("Run HRP"):
            try:
                hrp_weights = run_hrp(prices)
                st.write(hrp_weights)
                st.bar_chart(pd.Series(hrp_weights))
            except Exception as e:
                st.warning(f"HRP failed: {e}")

    st.divider()
    st.subheader("Monte Carlo Simulation (Value at Risk)")
    st.markdown(f"""
    **What is this?**
    We simulate thousands of possible future price paths for your **Entire Portfolio** (Equal-Weighted).
    *   **Assets Included**: {", ".join(tickers)}
    *   **VaR (Value at Risk)**: The maximum loss you might expect with 95% confidence.
    *   **CVaR (Conditional VaR)**: The average loss in the worst 5% of cases (a more conservative risk measure).
    """)
    
    sim_runs = st.slider("Simulations", 1000, 5000, 10000)
    
    if st.button("Run Simulation"):
        sims = run_monte_carlo(prices, simulations=sim_runs)
        
        # Plot Trajectories
        fig_mc = go.Figure()
        # Show only first 100 traces
        for i in range(min(1000, sim_runs)):
            fig_mc.add_trace(go.Scatter(y=sims[i,:], mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
        fig_mc.update_layout(title="Portfolio Monte Carlo Pathways", showlegend=False, template="plotly_dark")
        st.plotly_chart(fig_mc)
        
        # ... existing stats code ...
        final_values = sims[:, -1]
        var_95 = np.percentile(final_values, 5)
        cvar_95 = final_values[final_values <= var_95].mean()
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("VaR (95%)", f"${var_95:,.2f}")
        col_m2.metric("CVaR (95%)", f"${cvar_95:,.2f}")
        
        # Histogram
        fig_hist = go.Figure(data=[go.Histogram(x=final_values, nbinsx=50)])
        fig_hist.update_layout(title="Distribution of Final Portfolio Values", template="plotly_dark")
        st.plotly_chart(fig_hist)

# --- TAB: AI Forecast ---
with tab_ai:
    target_stock = st.selectbox("Select Asset for AI", prices.columns)
    
    col_ai_1, col_ai_2 = st.columns(2)
    
    with col_ai_1:
        st.markdown("### LSTM Price Prediction")
        if st.button("Train LSTM & Predict"):
            if not HAS_TF:
                st.error("TensorFlow is not installed. Please install it to use LSTM.")
            else:
                with st.spinner("Training Neural Network (20 Epochs)..."):
                    try:
                        pred_price, pred_log = run_lstm_prediction(prices[target_stock])
                        
                        if pred_price == 0.0:
                             st.warning("Not enough data to train.")
                        else:
                            current_price = prices[target_stock].iloc[-1]
                            delta = ((pred_price - current_price) / current_price) * 100
                            
                            st.metric("Current Price", f"${current_price:.2f}")
                            st.metric("LSTM Forecast (Next Day)", f"${pred_price:.2f}", f"{delta:.2f}%")
                            st.caption(f"Predicted Log Return: {pred_log:.5f}")
                    except Exception as e:
                        st.error(f"Prediction Error: {e}")
    
    with col_ai_2:
        st.markdown("### NLP Sentiment (FinBERT)")
        if st.button("Analyze Sentiment"):
            with st.spinner("Analyzing... (First run downloads model ~400MB)"):
                sentiment = get_finbert_sentiment(target_stock)
                st.info(f"Market Sentiment for {target_stock}: **{sentiment}**")