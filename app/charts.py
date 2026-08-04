import streamlit as st


def render_performance_chart(payload):
    st.subheader("Performance Visualizations")
    if hasattr(payload, "equity_curve") and payload.equity_curve is not None and not payload.equity_curve.empty:
        st.markdown("**Equity Curve**")
        st.line_chart(payload.equity_curve[["Portfolio_Value"]])
    else:
        st.info("No equity curve data available for this run.")
