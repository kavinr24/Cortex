import numpy as np
import streamlit as st


def _safe_value(metrics, key, fallback):
    value = metrics.get(key, fallback)
    if value is None:
        return fallback
    if isinstance(value, (float, int, np.floating, np.integer)):
        if not np.isfinite(value):
            return fallback
    return value


def render_summary_metrics(metrics):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total Return",
        _safe_value(metrics, "total_return", "0.00%"),
        help="Net return over the date range with friction costs.",
    )
    col2.metric(
        "Sharpe Ratio",
        _safe_value(metrics, "sharpe_ratio", "0.00"),
        help="Risk adjusted return measure calculated off of zero risk free rate.",
    )
    col3.metric(
        "Max Drawdown",
        _safe_value(metrics, "max_drawdown", "0.00%"),
        help="Maximum observed peak to trough decline in portfolio value.",
    )
    col4.metric(
        "Win Rate",
        _safe_value(metrics, "win_rate", "0.0%"),
        help="Percentage of closed trades that generated a positive return.",
    )
