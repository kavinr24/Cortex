import pandas as pd
import streamlit as st


def render_trade_history(payload, ticker, strategy_key):
    st.subheader("Executed Trades Log")
    if hasattr(payload, "trades") and payload.trades is not None and not payload.trades.empty:
        st.dataframe(payload.trades, use_container_width=True)
        csv_data = payload.trades.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Trade Log",
            data=csv_data,
            file_name=f"{ticker}_{strategy_key}_trades.csv",
            mime="text/csv",
        )
    else:
        st.info("No trades were generated during this backtest window.")


def render_detailed_metrics(metrics):
    st.subheader("Full Indicator Breakdown")
    metrics_df = pd.DataFrame(
        list(metrics.items()), columns=["Metric Indicator", "Calculated Value"]
    )
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
