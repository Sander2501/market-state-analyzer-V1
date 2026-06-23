# Market-State Analyzer

A Python + Streamlit market-state analysis and backtesting app for stocks, crypto, and forex.

## What it does

- Fetches market data
- Calculates SMA, EMA, RSI, and volatility
- Classifies market state
- Detects support and resistance
- Runs signal backtests
- Shows hit rate, average return, drawdown, Sharpe ratio
- Includes a watchlist scanner
- Exports results to CSV

## Important

This project does not predict prices and does not give financial advice.  
It describes market conditions and compares similar historical states.

## Run

```bash
source venv/bin/activate
streamlit run ui/streamlit_app.py
