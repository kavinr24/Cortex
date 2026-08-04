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
