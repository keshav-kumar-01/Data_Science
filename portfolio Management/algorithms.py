import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from pypfopt import risk_models, expected_returns, plotting, objective_functions
from pypfopt import BlackLittermanModel, EfficientFrontier, HRPOpt
from pypfopt import black_litterman
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings("ignore")

# Try to import Deep Learning libs
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    HAS_TF = True
except ImportError:
    HAS_TF = False

# ==========================================
# Data Utilities
# ==========================================

@st.cache_data
def load_market_caps(tickers):
    mcaps = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            mcaps[t] = stock.info.get('marketCap', 0)
        except:
            mcaps[t] = 0
    return mcaps

# ==========================================
# Phase 1: Advanced Algorithms
# ==========================================

def run_black_litterman(prices, market_prices, view_dict=None):
    # 1. Calculate Covariance Matrix & Delta
    try:
        S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
        delta = black_litterman.market_implied_risk_aversion(market_prices)
    except Exception as e:
        print(f"Error calculating covariance or delta: {e}")
        return {}
    
    # 2. Market Cap for Market Prior
    tickers = prices.columns.tolist()
    mcaps = load_market_caps(tickers)
    
    # 3. BL Model
    # Default view if none provided
    if not view_dict:
        view_dict = {tickers[0]: 0.10} # Example View
        
    bl = BlackLittermanModel(S, pi="market", market_caps=mcaps, risk_aversion=delta,
                             absolute_views=view_dict)
    
    # 4. Posterior Returns & Weights
    ret_bl = bl.bl_returns()
    S_bl = bl.bl_cov()
    
    ef = EfficientFrontier(ret_bl, S_bl)
    ef.add_objective(objective_functions.L2_reg)
    weights = ef.max_sharpe()
    return weights

def run_hrp(prices):
    returns = prices.pct_change().dropna()
    hrp = HRPOpt(returns)
    weights = hrp.optimize()
    return weights

def run_monte_carlo(prices, simulations=10000, time_horizon=252):
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    sim_results = np.zeros((simulations, time_horizon))
    last_price = 100 
    
    for i in range(simulations):
        daily_returns = np.random.multivariate_normal(mean_returns, cov_matrix, time_horizon)
        portfolio_daily_returns = daily_returns.mean(axis=1)
        cumulative_returns = np.cumprod(1 + portfolio_daily_returns)
        sim_results[i, :] = last_price * cumulative_returns
        
    return sim_results

# ==========================================
# Phase 2: ML & Deep Learning
# ==========================================

def run_lstm_prediction(stock_data):
    if not HAS_TF:
        return 0.0, 0.0
        
    # Use Log Returns for stationarity
    log_returns = np.log(stock_data / stock_data.shift(1)).dropna()
    
    # Data Prep
    data = log_returns.values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    # Create Sequences
    prediction_days = 60
    if len(scaled_data) < prediction_days + 10:
        return 0.0, 0.0 # Not enough data
        
    x_train, y_train = [], []
    
    for x in range(prediction_days, len(scaled_data)):
        x_train.append(scaled_data[x-prediction_days:x, 0])
        y_train.append(scaled_data[x, 0])
        
    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    
    # Build Model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(x_train, y_train, epochs=20, batch_size=32, verbose=0)
    
    # Predict Next Day Return
    real_data = [scaled_data[len(scaled_data) + 1 - prediction_days : len(scaled_data+1), 0]]
    real_data = np.array(real_data)
    real_data = np.reshape(real_data, (real_data.shape[0], real_data.shape[1], 1))
    
    prediction_scaled = model.predict(real_data)
    prediction_log_return = scaler.inverse_transform(prediction_scaled)[0][0]
    
    # Convert Log Return back to Price: P_next = P_current * e^r
    current_price = stock_data.iloc[-1]
    predicted_price = current_price * np.exp(prediction_log_return)
    
    return predicted_price, prediction_log_return

def get_finbert_sentiment(ticker):
    try:
        import os
        os.environ["TF_USE_LEGACY_KERAS"] = "1"
        from transformers import pipeline
        # Cache the pipeline to avoid reloading
        @st.cache_resource
        def load_sentiment_pipeline():
            return pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")
            
        nlp = load_sentiment_pipeline()
        
        dummy_news = [
            f"{ticker} reports strong earnings growth and positive outlook.",
            f"{ticker} faces regulatory scrutiny and potential fines.",
            f"{ticker} announces new product launch and expansion plans."
        ]
        import random
        text = random.choice(dummy_news)
        
        result = nlp(text)[0]
        return f"{result['label']} (Conf: {result['score']:.2f}) based on: '{text}'"
    except Exception as e:
        return f"Error: {str(e)}"
