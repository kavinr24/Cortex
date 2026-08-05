import json
import sys
from pathlib import Path

import streamlit as st
from bridge import CortexBridge

sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))

from charts import render_performance_chart
from metrics import render_summary_metrics
from sidebar import render_sidebar
from tables import render_detailed_metrics, render_trade_history
from builder_ui import render_strategy_builder

st.set_page_config(
    page_title="Cortex Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_bridge() -> CortexBridge:
    return CortexBridge()


bridge = get_bridge()

st.title("Cortex Engine")

(
    ticker,
    selected_strategy_label,
    strategy_key,
    start_date,
    end_date,
    strategy_params,
    initial_capital,
    commission_pct,
    slippage_pct,
    run_button,
) = render_sidebar()

# Option to open the Strategy Builder
use_builder = st.sidebar.checkbox("Open Strategy Builder", value=False)

if use_builder:
    # load data for the selected ticker
    df_loaded, data_log = bridge._load_data(symbol=ticker, timeframe="1D")
    # normalize columns to lowercase
    df_preview = df_loaded.copy()
    if df_preview.index.name is not None:
        df_preview = df_preview.reset_index()
    df_preview.columns = [c.lower() for c in df_preview.columns]

    # add standard technical indicators
    if "close" in df_preview.columns:
        df_preview["sma_10"] = df_preview["close"].rolling(window=10, min_periods=1).mean()
        df_preview["sma_30"] = df_preview["close"].rolling(window=30, min_periods=1).mean()
        df_preview["ema_9"] = df_preview["close"].ewm(span=9, adjust=False).mean()

        # drop initial rows where rolling indicators may be NaN (keep rows where indicators are valid)
        df_preview = df_preview.dropna(subset=["sma_10", "sma_30", "ema_9"]).reset_index(drop=True)

    strategy = render_strategy_builder(df_preview)
    if strategy is not None:
        st.success("Strategy built — previewing generated signals below")
        st.dataframe(strategy.tail(20))
        csv = strategy.to_csv(index=False).encode("utf-8")
        st.download_button("Download Signals CSV", data=csv, file_name=f"{ticker}_signals.csv", mime="text/csv")
    st.divider()

if run_button:
    if start_date >= end_date:
        st.error("Invalid execution time window. The start date must be earlier than end date.")
    else:
        with st.spinner(f"Running {selected_strategy_label} on {ticker}..."):
            payload = bridge.execute_backtest(
                {
                    "symbol": ticker,
                    "strategy": strategy_key,
                    "strategy_params": strategy_params,
                    "capital": int(initial_capital),
                    "commission": float(commission_pct),
                    "slippage": float(slippage_pct),
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                }
            )

        st.success(
            f"Execution completed for **{ticker.upper()}** with **{selected_strategy_label}**"
        )

        metrics = payload.metrics or {}
        render_summary_metrics(metrics)

        st.divider()

        tab_charts, tab_trades, tab_metrics, tab_raw = st.tabs(
            ["Performance Charts", "Trade History", "Detailed Metrics", "Export & Debug"]
        )

        with tab_charts:
            render_performance_chart(payload)

        with tab_trades:
            render_trade_history(payload, ticker, strategy_key)

        with tab_metrics:
            render_detailed_metrics(metrics)

        with tab_raw:
            st.subheader("Export & Bridge Payload")
            report_payload = {
                "ticker": ticker,
                "strategy": selected_strategy_label,
                "execution_window": {
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                },
                "parameters": strategy_params,
                "friction": {
                    "initial_capital": int(initial_capital),
                    "commission_pct": float(commission_pct),
                    "slippage_pct": float(slippage_pct),
                },
                "metrics": metrics,
                "logs": getattr(payload, "logs", []),
            }
            st.json(report_payload)
            json_report = json.dumps(report_payload, indent=4).encode("utf-8")
            st.download_button(
                label="Download Full Backtest Report",
                data=json_report,
                file_name=f"{ticker}_{strategy_key}_report.json",
                mime="application/json",
            )
else:
    st.info("Configure your backtest parameters in the sidebar and click Run Backtest to start backtesting.")
