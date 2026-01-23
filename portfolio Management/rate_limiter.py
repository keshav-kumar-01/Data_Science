"""
Rate Limiter for Yahoo Finance API calls
Implements auto-throttling and session management
"""
import time
import yfinance as yf
from datetime import datetime, timedelta
from functools import wraps
import streamlit as st
import pandas as pd

class YFinanceRateLimiter:
    def __init__(self, calls_per_minute=15, min_delay=2.0):
        self.calls_per_minute = calls_per_minute
        self.min_delay = min_delay  # Minimum delay between calls
        self.call_times = []
        self.last_call = 0
        
    def wait_if_needed(self):
        """Ultra-conservative auto-throttle"""
        now = time.time()
        
        # Enforce minimum delay between ANY calls
        time_since_last = now - self.last_call
        if time_since_last < self.min_delay:
            wait = self.min_delay - time_since_last
            time.sleep(wait)
            now = time.time()
        
        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]
        
        # If we've made too many calls, wait
        if len(self.call_times) >= self.calls_per_minute:
            wait_time = 60 - (now - self.call_times[0]) + 5  # Add 5s buffer
            if wait_time > 0:
                st.info(f"⏳ Rate limit protection: Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                self.call_times = []
        
        # Add current call
        self.call_times.append(time.time())
        self.last_call = time.time()
    
    def download_single_ticker(self, ticker, start, end, max_retries=3):
        """Download a single ticker with retry logic"""
        for attempt in range(max_retries):
            try:
                self.wait_if_needed()
                
                # Use Ticker object for more reliable downloads
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(start=start, end=end, auto_adjust=True)
                
                if not hist.empty and 'Close' in hist.columns:
                    return hist['Close']
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                if 'rate' in error_msg or 'limit' in error_msg or '429' in error_msg:
                    wait_time = (2 ** attempt) * 15  # 15s, 30s, 60s
                    st.warning(f"⚠️ Rate limit for {ticker}. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    if attempt == max_retries - 1:
                        st.warning(f"⚠️ Could not load {ticker}: {str(e)[:50]}")
                    time.sleep(2)
        
        return None
    
    def download_with_retry(self, tickers, start, end, max_retries=3):
        """Standard yfinance download with retry logic for small lists/benchmarks"""
        if not isinstance(tickers, list):
            tickers = [tickers]
            
        for attempt in range(max_retries):
            try:
                self.wait_if_needed()
                data = yf.download(
                    tickers, 
                    start=start, 
                    end=end, 
                    group_by='ticker',
                    progress=False,
                    threads=False,
                    auto_adjust=True
                )
                if not data.empty:
                    return data
            except Exception as e:
                if "rate" in str(e).lower() or "429" in str(e).lower():
                    wait = (2 ** attempt) * 15
                    st.warning(f"⚠️ Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
        return None

    def download_in_batches(self, tickers, start, end):
        """Download tickers in SMALL batches for reliability"""
        all_data = {}
        batch_size = 5  # Increased slightly for better speed, but still safe
        
        # Split into batches
        batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        successful = 0
        failed = []
        
        for idx, batch in enumerate(batches):
            status_text.text(f"📊 Loading batch {idx + 1}/{len(batches)}: {', '.join(batch[:3])}...")
            
            # Try to download batch as a whole first (faster)
            data = None
            try:
                self.wait_if_needed()
                data = yf.download(batch, start=start, end=end, group_by='ticker', progress=False, threads=False, auto_adjust=True)
            except:
                pass

            if data is not None and not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    for ticker in batch:
                        try:
                            if ticker in data.columns.levels[0]:
                                # Force clean numeric column
                                col = data[ticker]['Close']
                                if not col.empty:
                                    all_data[ticker] = col
                                    successful += 1
                                else:
                                    failed.append(ticker)
                        except:
                            # Fallback to individual download if batch extract fails
                            ind_data = self.download_single_ticker(ticker, start, end)
                            if ind_data is not None:
                                all_data[ticker] = ind_data
                                successful += 1
                            else:
                                failed.append(ticker)
                else:
                    # Single ticker batch
                    if 'Close' in data.columns:
                        all_data[batch[0]] = data['Close']
                        successful += 1
            else:
                # Batch failed, try individually
                for ticker in batch:
                    ind_data = self.download_single_ticker(ticker, start, end)
                    if ind_data is not None:
                        all_data[ticker] = ind_data
                        successful += 1
                    else:
                        failed.append(ticker)
            
            # Update progress
            progress_bar.progress((idx + 1) / len(batches))
        
        progress_bar.empty()
        status_text.empty()
        
        # Show summary
        if successful > 0:
            st.success(f"✅ Successfully loaded {successful}/{len(tickers)} tickers")
        if failed:
            failed = list(set(failed))
            st.warning(f"⚠️ Failed to load {len(failed)} tickers: {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")
        
        return pd.DataFrame(all_data)

# Global rate limiter instance - Adjusted for better performance balance
rate_limiter = YFinanceRateLimiter(calls_per_minute=20, min_delay=1.5)
