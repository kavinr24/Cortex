import streamlit as st
import pandas as pd


def render_performance_chart(payload):
    st.subheader("Performance Visualizations")
    if hasattr(payload, "equity_curve") and payload.equity_curve is not None and not payload.equity_curve.empty:
        st.markdown("**Equity Curve**")
        equity = payload.equity_curve
        if "Portfolio_Value" not in equity.columns:
            st.info("No equity curve data available for this run.")
            return
        chart_df = pd.to_numeric(equity["Portfolio_Value"], errors="coerce").to_frame("Portfolio_Value").dropna()
        if chart_df.empty:
            st.info("No equity curve data available for this run.")
        else:
            st.line_chart(chart_df)
    else:
        st.info("No equity curve data available for this run.")
