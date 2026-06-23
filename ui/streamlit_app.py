import re

import pandas as pd
import streamlit as st

from backtesting.engine import backtest_market_state
from backtesting.monte_carlo import monte_carlo_simulation
from backtesting.walk_forward import walk_forward_analysis
from core.ai_explanation import explain_market_state
from core.charts import create_candlestick_chart
from core.confidence import small_sample_note
from core.config import (
    DEFAULT_HOLDING_DAYS,
    DEFAULT_STOP_ATR_MULTIPLIER,
    DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER,
    DEFAULT_TRANSACTION_COST_PCT,
    LOW_CONFIDENCE_TRADES,
)
from core.explanations import explain_signal
from core.indicators import add_indicators
from core.market_state import analyze_market_state
from core.portfolio import analyze_portfolio
from core.report import create_report
from core.risk import calculate_atr_stops, calculate_position_size, calculate_risk_reward
from core.scanner import scan_watchlist
from core.structure import analyze_structure
from data.providers import get_price_data

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.=\-_/]+$")


def clean_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def parse_symbols(text: str) -> list[str]:
    return [clean_symbol(symbol) for symbol in text.split(",") if clean_symbol(symbol)]


def validate_symbols(symbols: list[str]) -> list[str]:
    return [symbol for symbol in symbols if not SYMBOL_PATTERN.match(symbol)]


def periods_per_year_for_interval(interval: str) -> int:
    return 52 if interval == "1wk" else 252


def show_methodology() -> None:
    with st.expander("Methodology and limitations", expanded=False):
        st.markdown(
            f"""
            - **Market state** uses moving averages, RSI, volatility, and recent range structure.
            - **Backtests** compare historical occurrences of the same rule-based signal.
            - **Confidence labels** are based only on sample count: low confidence is fewer than {LOW_CONFIDENCE_TRADES} trades.
            - **Risk exits** are optional ATR-based stop-loss/take-profit exits. If both stop and take profit are touched in one bar, the stop is assumed first.
            - **Walk-forward** is a sequential date split with fixed rules, not fitted parameter optimization.
            - **Monte Carlo** resamples historical trade returns. It does not predict future prices.
            """
        )


st.title("Market-State Analyzer")
show_methodology()

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
    value=DEFAULT_HOLDING_DAYS,
)

transaction_cost_pct = st.slider(
    "Transaction cost (%)",
    min_value=0.0,
    max_value=1.0,
    value=DEFAULT_TRANSACTION_COST_PCT,
    step=0.05,
)

use_risk_exits = st.checkbox("Use ATR stop-loss/take-profit exits in backtests")

if use_risk_exits:
    col1, col2 = st.columns(2)
    backtest_stop_atr = col1.slider(
        "Backtest stop ATR multiplier",
        1.0,
        5.0,
        DEFAULT_STOP_ATR_MULTIPLIER,
        0.5,
    )
    backtest_take_profit_atr = col2.slider(
        "Backtest take-profit ATR multiplier",
        1.0,
        10.0,
        DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER,
        0.5,
    )
else:
    backtest_stop_atr = DEFAULT_STOP_ATR_MULTIPLIER
    backtest_take_profit_atr = DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER

refresh_data = st.checkbox("Refresh data instead of using cache")


if mode == "Single Symbol Analysis":
    symbol_input = st.text_input("Symbol", value="AAPL")
    symbol = clean_symbol(symbol_input)

    if st.button("Analyze"):
        invalid_symbols = validate_symbols([symbol])
        if not symbol:
            st.error("Enter a symbol before running analysis.")
        elif invalid_symbols:
            st.error(f"Invalid symbol format: {invalid_symbols[0]}")
        else:
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
                    periods_per_year=periods_per_year_for_interval(interval),
                    use_risk_exits=use_risk_exits,
                    stop_atr_multiplier=backtest_stop_atr,
                    take_profit_atr_multiplier=backtest_take_profit_atr,
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
                    "Confidence": result["confidence"],
                    "Hit Rate (%)": result["hit_rate"],
                    "Average Return (%)": result["average_return"],
                    "Max Drawdown (%)": result["max_drawdown"],
                    "Best Trade (%)": result["best_trade"],
                    "Worst Trade (%)": result["worst_trade"],
                    "Win/Loss Ratio": result["win_loss_ratio"],
                    "Sharpe Ratio": result["sharpe_ratio"],
                    "Sample Caveat": small_sample_note(result["signals"]),
                })

            if any(result["signals"] < LOW_CONFIDENCE_TRADES for result in signals_backtest.values()):
                st.warning(
                    "Some backtest rows are based on low sample counts. "
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
            atr_sl_mult = st.slider(
                "Stop loss ATR multiplier",
                1.0,
                4.0,
                DEFAULT_STOP_ATR_MULTIPLIER,
                0.5,
                key="atr_sl",
            )
            atr_tp_mult = st.slider(
                "Take profit ATR multiplier",
                1.0,
                8.0,
                DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER,
                0.5,
                key="atr_tp",
            )

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
            periods_per_year=periods_per_year_for_interval(interval),
        )

        if wf["note"]:
            st.write(wf["note"])
        elif not wf["folds"]:
            st.write("No out-of-sample trades were generated.")
        else:
            wf_df = pd.DataFrame(wf["folds"])
            if (wf_df["test_trades"] < LOW_CONFIDENCE_TRADES).any():
                st.warning(
                    "One or more out-of-sample folds has a low trade count. "
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
        symbols = parse_symbols(watchlist_text)
        invalid_symbols = validate_symbols(symbols)

        if not symbols:
            st.error("Enter at least one symbol to scan.")
        elif invalid_symbols:
            st.error(f"Invalid symbol format: {', '.join(invalid_symbols)}")
        else:
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
        symbols = parse_symbols(portfolio_text)
        invalid_symbols = validate_symbols(symbols)

        if not symbols:
            st.error("Enter at least two symbols to analyze a portfolio.")
        elif invalid_symbols:
            st.error(f"Invalid symbol format: {', '.join(invalid_symbols)}")
        else:
            with st.spinner("Analyzing portfolio..."):
                portfolio = analyze_portfolio(
                    symbols=symbols,
                    period=period,
                    interval=interval,
                    refresh=refresh_data,
                    periods_per_year=periods_per_year_for_interval(interval),
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
