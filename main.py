from backtesting.engine import backtest_market_state
from core.indicators import add_indicators
from core.market_state import analyze_market_state
from core.report import create_report
from data.providers import get_price_data


def main():
    symbol = input("Enter symbol, for example AAPL, MSFT, BTC-USD: ")

    data = get_price_data(symbol)
    data = add_indicators(data)

    analysis = analyze_market_state(data)
    backtest = backtest_market_state(data)

    report = create_report(symbol, analysis, backtest)

    print(report)


if __name__ == "__main__":
    main()
