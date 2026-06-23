import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from data.providers import get_price_data
from core.indicators import add_indicators
from core.market_state import analyze_market_state
from core.structure import analyze_structure
from core.explanations import explain_signal
from core.scanner import scan_watchlist
from core.charts import create_candlestick_chart
from backtesting.engine import backtest_market_state
from core.report import create_report


st.title("Market-State Analyzer")

mode = st.radio(
    "Mode",
    ["Single Symbol Analysis", "Watchlist Scanner"],
)

period = st.selectbox(
    "Period",
    ["6mo", "1y", "2y", "5y"],
    index=1,
)

interval = st.selectbox(
    "Interval",
    ["1d", "1wk"],
    index=0,
)

holding_days = st.slider(
    "Backtest holding days",
    min_value=5,
    max_value=30,
    value=10,
)

transaction_cost_pct = st.slider(
    "Transaction cost (%)",
    min_value=0.0,
    max_value=1.0,
    value=0.1,
    step=0.05,
)

refresh_data = st.checkbox("Refresh data instead of using cache")


if mode == "Single Symbol Analysis":
    symbol = st.text_input("Symbol", value="AAPL")

    if st.button("Analyze"):
        try:
            data = get_price_data(
                symbol,
                period=period,
                interval=interval,
                refresh=refresh_data,
            )

            data = add_indicators(data)

            analysis = analyze_market_state(data)
            structure = analyze_structure(data)
            explanation = explain_signal(analysis, structure)

            backtest = backtest_market_state(
                data,
                holding_days=holding_days,
                transaction_cost_pct=transaction_cost_pct,
            )

            report = create_report(
                symbol,
                analysis,
                backtest["signals"],
                structure,
                explanation,
            )

            st.success("Analysis completed.")

            st.subheader("Current Metrics")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Close", analysis["close"])
            col2.metric("Trend", analysis["trend"])
            col3.metric("RSI", analysis["rsi"])
            col4.metric("Signal", analysis["signal"])

            st.subheader("Market Structure")

            col1, col2, col3 = st.columns(3)

            col1.metric("Support", structure["support"])
            col2.metric("Resistance", structure["resistance"])
            col3.metric("Location", structure["location"])

            st.subheader("Signal Explanation")
            st.text(explanation)

            st.subheader("Price Chart")
            fig = create_candlestick_chart(
                data,
                symbol,
                support=structure["support"],
                resistance=structure["resistance"],
            )
            st.plotly_chart(fig, width="stretch")

            st.subheader("Backtest by Signal Type")

            signals_backtest = backtest["signals"]

            if not signals_backtest:
                st.write("No signals found for this period.")
            else:
                rows = []

                for signal_name, result in signals_backtest.items():
                    rows.append({
                        "Signal": signal_name,
                        "Signals Found": result["signals"],
                        "Hit Rate (%)": result["hit_rate"],
                        "Average Return (%)": result["average_return"],
                        "Max Drawdown (%)": result["max_drawdown"],
                        "Best Trade (%)": result["best_trade"],
                        "Worst Trade (%)": result["worst_trade"],
                        "Win/Loss Ratio": result["win_loss_ratio"],
                        "Sharpe Ratio": result["sharpe_ratio"],
                    })

                backtest_df = pd.DataFrame(rows)
                st.dataframe(backtest_df, width="stretch")

            st.subheader("Benchmark")
            st.write(
                f"Buy and hold return: "
                f"{backtest['benchmark']['buy_and_hold_return']}%"
            )

            st.subheader("Trade Log")

            trade_log_df = pd.DataFrame(backtest["trade_log"])

            if trade_log_df.empty:
                st.write("No trades found.")
            else:
                st.dataframe(trade_log_df, width="stretch")

                csv = trade_log_df.to_csv(index=False)

                st.download_button(
                    label="Download trade log as CSV",
                    data=csv,
                    file_name=f"{symbol}_trade_log.csv",
                    mime="text/csv",
                )

            st.subheader("Full Report")
            st.text(report)

        except Exception as e:
            st.error(f"Something went wrong: {e}")


else:
    default_watchlist = "AAPL,MSFT,NVDA,AMD,TSLA,BTC-USD,ETH-USD,EURUSD=X"

    watchlist_text = st.text_area(
        "Watchlist symbols, separated by commas",
        value=default_watchlist,
    )

    if st.button("Scan Watchlist"):
        symbols = [
            symbol.strip().upper()
            for symbol in watchlist_text.split(",")
            if symbol.strip()
        ]

        with st.spinner("Scanning watchlist..."):
            scan_results = scan_watchlist(
                symbols=symbols,
                period=period,
                interval=interval,
                holding_days=holding_days,
                transaction_cost_pct=transaction_cost_pct,
                refresh=refresh_data,
            )

        scanner_df = pd.DataFrame(scan_results)

        if "Score" in scanner_df.columns:
            scanner_df = scanner_df.sort_values(
                by="Score",
                ascending=False,
            )

        st.subheader("Watchlist Results")
        st.dataframe(scanner_df, width="stretch")

        csv = scanner_df.to_csv(index=False)

        st.download_button(
            label="Download scanner results as CSV",
            data=csv,
            file_name="watchlist_scan.csv",
            mime="text/csv",
        )
