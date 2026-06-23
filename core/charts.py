import pandas as pd
import plotly.graph_objects as go


def create_candlestick_chart(
    data: pd.DataFrame,
    symbol: str,
    support: float | None = None,
    resistance: float | None = None,
):
    df = data.dropna().copy()

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_20"],
            mode="lines",
            name="SMA 20",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_50"],
            mode="lines",
            name="SMA 50",
        )
    )

    if support is not None:
        fig.add_hline(
            y=support,
            line_dash="dash",
            annotation_text="Support",
            annotation_position="bottom right",
        )

    if resistance is not None:
        fig.add_hline(
            y=resistance,
            line_dash="dash",
            annotation_text="Resistance",
            annotation_position="top right",
        )

    fig.update_layout(
        title=f"{symbol} Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600,
    )

    return fig
