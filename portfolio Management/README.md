# In-House Bloomberg Terminal v2.0

A comprehensive financial analysis platform built with Streamlit, featuring advanced portfolio optimization, machine learning predictions, and global market coverage.

## 🚀 Features

### 📊 Analysis & Data
- **Deep Asset Analysis (FA/DES)**: Company descriptions, financial metrics, analyst recommendations
- **ESG Data**: Environmental, Social, and Governance scores
- **Supply Chain Analysis (SPLC)**: Supplier and customer mapping
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Candlestick charts

### 🌍 Global Market Coverage
- **India (NIFTY 50)**: 35+ stocks
- **US (NYSE & NASDAQ)**: 50+ stocks
- **EU (London & Euronext)**: 30+ stocks
- **Japan (Tokyo)**: 20+ stocks
- **China (Shanghai & Shenzhen)**: 16+ stocks
- **Hong Kong**: 20+ stocks
- **Commodities & FX**: Gold, Oil, Bitcoin, Currency pairs

### ⚖️ Portfolio Optimization
- **Black-Litterman Model**: Combine market equilibrium with your views
- **Hierarchical Risk Parity (HRP)**: ML-based correlation clustering
- **Monte Carlo Simulation**: VaR and CVaR risk analysis

### 🤖 AI & Machine Learning
- **LSTM Price Prediction**: Deep learning forecasts using log returns
- **FinBERT Sentiment Analysis**: NLP-based market sentiment

### 🗺️ Additional Features
- **Terminal Map**: Global shipping and flight tracking visualization
- **POSH**: Luxury classifieds (yachts, jets, real estate)
- **DINE**: Elite restaurant recommendations
- **BQL Excel Integration**: Export data to CSV

## 📦 Installation

```bash
# Install dependencies
pip install streamlit yfinance pandas numpy plotly pandas_ta PyPortfolioOpt tensorflow transformers torch scikit-learn

# Run the application
streamlit run app.py
```

## ⚠️ Rate Limit Management

Yahoo Finance has rate limits. To avoid issues:

1. **Cache Duration**: Data is cached for 1 hour
2. **Request Delays**: Automatic 0.5-1 second delays between requests
3. **Best Practices**:
   - Select fewer market groups (max 2-3 at once)
   - Use shorter date ranges (1-2 years instead of 5+)
   - Wait 60 seconds if you hit a rate limit
   - Avoid refreshing the page repeatedly

## 🎯 Usage Tips

### Getting Started
1. **Select Markets**: Use the sidebar to choose market groups
2. **Date Range**: Set your analysis period (shorter = faster)
3. **Ticker Selection**: In "My Portfolio", select specific stocks to compare

### Avoiding Rate Limits
- **Start Small**: Begin with 1-2 market groups
- **Use Cache**: Data is cached for 1 hour - avoid changing date ranges frequently
- **Sequential Loading**: Let one tab load completely before switching to another
- **Wait on Errors**: If you see a rate limit error, wait 60 seconds

### Recommended Workflow
1. Load US markets first (most reliable)
2. Analyze your portfolio in "My Portfolio" tab
3. Run optimizations in "Optimization" tab
4. Check AI predictions last (requires additional model downloads)

## 🛠️ Technical Details

- **Data Source**: Yahoo Finance (yfinance)
- **Caching**: Streamlit cache with 1-hour TTL
- **Rate Limiting**: Built-in delays and retry logic
- **ML Models**: TensorFlow (LSTM), Hugging Face Transformers (FinBERT)

## 📝 Notes

- First-time FinBERT usage downloads ~400MB model
- LSTM training takes 30-60 seconds per ticker
- Some international tickers may have limited data availability
- Rate limits are per IP address - shared networks may hit limits faster

## 🐛 Troubleshooting

**Rate Limit Error**:
- Wait 60 seconds
- Reduce number of selected tickers
- Use a shorter date range

**No Data Loaded**:
- Check ticker symbols are correct
- Verify date range is valid
- Some tickers may not have historical data

**Slow Performance**:
- Reduce number of selected tickers
- Disable technical indicators temporarily
- Use cached data (avoid changing dates)
