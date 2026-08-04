import streamlit as st


def render_summary_metrics(metrics):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total Return",
        metrics.get("total_return", "0.00%"),
        help="Net return over the date range with friction costs.",
    )
    col2.metric(
        "Sharpe Ratio",
        metrics.get("sharpe_ratio", "0.00"),
        help="Risk adjusted return measure calculated off of zero risk free rate.",
    )
    col3.metric(
        "Max Drawdown",
        metrics.get("max_drawdown", "0.00%"),
        help="Maximum observed peak to trough decline in portfolio value.",
    )
    col4.metric(
        "Win Rate",
        metrics.get("win_rate", "0.0%"),
        help="Percentage of closed trades that generated a positive return.",
    )
