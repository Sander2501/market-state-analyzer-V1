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
from core.risk import calculate_risk_reward, calculate_atr_stops, calculate_position_size
from backtesting.walk_forward import walk_forward_analysis
from backtesting.monte_carlo import monte_carlo_simulation
from core.portfolio import analyze_portfolio
from core.ai_explanation import explain_market_state


def sample_size_note(count: int | None, threshold: int = 10) -> str:
    if count is None:
        return "No matching historical sample."
    if count < threshold:
        return f"Small sample ({count}); treat these metrics as unstable."
    return ""


st.title("Market-State Analyzer")

mode = st.radio(
    "Mode",
    ["Single Symbol Analysis", "Watchlist Scanner", "Portfolio Analyzer"],
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
                periods_per_year=52 if interval == "1wk" else 252,
            )

            report = create_report(
                symbol,
                analysis,
                backtest["signals"],
                structure,
                explanation,
            )

            st.session_state["analysis_result"] = {
                "symbol": symbol,
                "data": data,
                "analysis": analysis,
                "structure": structure,
                "explanation": explanation,
                "backtest": backtest,
                "report": report,
            }
        except Exception as e:
            st.session_state.pop("analysis_result", None)
            st.error(f"Something went wrong: {e}")

    result = st.session_state.get("analysis_result")

    if result:
        symbol = result["symbol"]
        data = result["data"]
        analysis = result["analysis"]
        structure = result["structure"]
        explanation = result["explanation"]
        backtest = result["backtest"]
        report = result["report"]

        st.subheader("Current Metrics")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Close", analysis["close"])
        col2.metric("Trend", analysis["trend"])
        col3.metric("RSI", analysis["rsi"])
        col4.metric("Signal", analysis["signal"])

        st.subheader("Market Regime")

        regime_detail = analysis["regime_detail"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Regime", analysis["regime"])
        col2.metric("Trend strength", f"{regime_detail['trend_strength_pct']}%")
        col3.metric("Volatility ratio", regime_detail["volatility_ratio"])
        st.caption(regime_detail["description"])

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
                    "Sample Caveat": sample_size_note(result["signals"]),
                })

            if any(result["signals"] < 10 for result in signals_backtest.values()):
                st.warning(
                    "Some backtest rows are based on fewer than 10 matching signals. "
                    "Hit rate, Sharpe ratio, and average return can swing heavily with samples that small."
                )

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

        st.subheader("Risk Calculator")

        latest_close = float(analysis["close"])
        latest_atr = float(data["ATR_14"].dropna().iloc[-1])

        with st.expander("ATR-Based Stops (auto-filled from live data)", expanded=True):
            atr_sl_mult = st.slider("Stop loss ATR multiplier", 1.0, 4.0, 2.0, 0.5, key="atr_sl")
            atr_tp_mult = st.slider("Take profit ATR multiplier", 1.0, 8.0, 4.0, 0.5, key="atr_tp")

            atr_stops = calculate_atr_stops(latest_close, latest_atr, atr_sl_mult, atr_tp_mult)

            st.caption(f"ATR(14) = {atr_stops['atr']}")

            col1, col2 = st.columns(2)
            col1.metric("ATR Stop Loss", atr_stops["stop_loss"])
            col2.metric("ATR Take Profit", atr_stops["take_profit"])

            rr_atr = calculate_risk_reward(latest_close, atr_stops["stop_loss"], atr_stops["take_profit"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Risk", f"{rr_atr['risk_pct']}%")
            col2.metric("Reward", f"{rr_atr['reward_pct']}%")
            col3.metric("R:R Ratio", f"1 : {rr_atr['ratio']}")

        with st.expander("Manual Risk/Reward", expanded=False):
            col1, col2, col3 = st.columns(3)
            entry_price = col1.number_input("Entry price", value=latest_close, min_value=0.0001, format="%.4f")
            stop_price = col2.number_input("Stop loss", value=round(latest_close * 0.97, 4), min_value=0.0001, format="%.4f")
            tp_price = col3.number_input("Take profit", value=round(latest_close * 1.06, 4), min_value=0.0001, format="%.4f")

            rr = calculate_risk_reward(entry_price, stop_price, tp_price)

            col1, col2, col3 = st.columns(3)
            col1.metric("Risk", f"{rr['risk_pct']}%")
            col2.metric("Reward", f"{rr['reward_pct']}%")
            col3.metric("R:R Ratio", f"1 : {rr['ratio']}")

        with st.expander("Position Sizing", expanded=False):
            col1, col2 = st.columns(2)
            account_size = col1.number_input("Account size", value=10000.0, min_value=1.0, step=500.0)
            risk_per_trade = col2.number_input("Risk per trade (%)", value=1.0, min_value=0.1, max_value=10.0, step=0.1)

            pos = calculate_position_size(account_size, risk_per_trade, latest_close, atr_stops["stop_loss"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Max loss", pos["max_loss"])
            col2.metric("Units to buy", pos["units"])
            col3.metric("Position value", pos["position_value"])

        st.subheader("Market-State Explanation")

        explanation_pair = explain_market_state(symbol, analysis, structure, backtest)
        st.write(explanation_pair["templated"])
        st.caption("Generated directly from the live stats and backtest output; no external AI API is used.")

        st.subheader("Walk-Forward Testing")
        st.caption(
            "Out-of-sample date-split evaluation: the data is split into sequential folds and "
            "each test window is scored on its own later period."
        )

        wf = walk_forward_analysis(
            data,
            n_splits=4,
            holding_days=holding_days,
            transaction_cost_pct=transaction_cost_pct,
            periods_per_year=52 if interval == "1wk" else 252,
        )

        if wf["note"]:
            st.write(wf["note"])
        elif not wf["folds"]:
            st.write("No out-of-sample trades were generated.")
        else:
            wf_df = pd.DataFrame(wf["folds"])
            if (wf_df["test_trades"] < 10).any():
                st.warning(
                    "One or more out-of-sample folds has fewer than 10 trades. "
                    "Use those fold metrics as directional context, not precise estimates."
                )
            st.dataframe(wf_df, width="stretch")
            agg = wf["aggregate"]
            col1, col2, col3 = st.columns(3)
            col1.metric("OOS trades", agg["trades"])
            col2.metric("OOS hit rate", f"{agg['hit_rate']}%" if agg["hit_rate"] is not None else "n/a")
            col3.metric("OOS avg return", f"{agg['average_return']}%" if agg["average_return"] is not None else "n/a")

        st.subheader("Monte Carlo Simulation")
        st.caption(
            "Resamples the historical trades 1000 times to show the range of equity "
            "curves that could have resulted from the same trade outcomes."
        )

        trade_returns = [row["Return (%)"] / 100 for row in backtest["trade_log"]]
        mc = monte_carlo_simulation(trade_returns, n_simulations=1000)

        if mc.get("note"):
            st.write(mc["note"])
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Expected return", f"{mc['expected_return']}%")
            col2.metric("Best case (95th)", f"{mc['best_case']}%")
            col3.metric("Worst case (5th)", f"{mc['worst_case']}%")

            col1, col2, col3 = st.columns(3)
            col1.metric("Worst drawdown", f"{mc['worst_drawdown']}%")
            col2.metric("Median drawdown", f"{mc['median_drawdown']}%")
            col3.metric("Probability of profit", f"{mc['probability_of_profit']}%")

            curve_df = pd.DataFrame(mc["sample_curves"]).transpose()
            st.line_chart(curve_df)

        st.subheader("Full Report")
        st.text(report)


elif mode == "Watchlist Scanner":
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

        if "Hit Rate (%)" in scanner_df.columns:
            st.caption(
                "Scanner scores use historical signal samples from the selected period. "
                "Thin samples can make rankings noisy, especially on short periods or weekly data."
            )

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


else:
    st.subheader("Portfolio Analyzer")
    st.caption(
        "Combines the symbols into an equal-weight portfolio and reports its "
        "annualized return, volatility, correlation matrix, and a diversification score."
    )

    default_portfolio = "AAPL,MSFT,NVDA,BTC-USD"

    portfolio_text = st.text_area(
        "Portfolio symbols, separated by commas",
        value=default_portfolio,
    )

    if st.button("Analyze Portfolio"):
        symbols = [
            symbol.strip().upper()
            for symbol in portfolio_text.split(",")
            if symbol.strip()
        ]

        with st.spinner("Analyzing portfolio..."):
            portfolio = analyze_portfolio(
                symbols=symbols,
                period=period,
                interval=interval,
                refresh=refresh_data,
                periods_per_year=52 if interval == "1wk" else 252,
            )

        if portfolio.get("note"):
            st.warning(portfolio["note"])
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Annual return", f"{portfolio['annual_return_pct']}%")
            col2.metric("Annual volatility", f"{portfolio['annual_volatility_pct']}%")
            col3.metric("Diversification score", f"{portfolio['diversification_score']}/100")

            st.caption(
                f"Equal weight: {portfolio['weight_each_pct']}% each. "
                f"Average pairwise correlation: {portfolio['average_correlation']}."
            )

            st.markdown("**Correlation matrix**")
            st.dataframe(portfolio["correlation_matrix"], width="stretch")

            st.markdown("**Annualized volatility per symbol**")
            st.dataframe(
                pd.DataFrame.from_dict(
                    portfolio["per_symbol_volatility_pct"],
                    orient="index",
                    columns=["Volatility (%)"],
                ),
                width="stretch",
            )

        if portfolio.get("errors"):
            st.error(f"Could not load: {portfolio['errors']}")
