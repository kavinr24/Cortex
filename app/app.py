from pathlib import Path
import sys
import pandas as pd
import streamlit as st
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge import CortexBridge


st.set_page_config(
    page_title="Cortex Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Cortex Engine")

@st.cache_resource
def get_bridge() -> CortexBridge:
    return CortexBridge()

bridge = get_bridge()

st.sidebar.header("Strategy Settings")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL")
strategy_type = st.sidebar.selectbox(
    "Strategy Model",
    ["Moving Average Crossover", "RSI Mean Reversion", "Buy & Hold Benchmark"],
)
st.sidebar.divider()
st.sidebar.header("Capital & Portfolio")
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)", min_value=1000, value=100000, step=5000
)

st.sidebar.divider()
st.sidebar.header("Friction Modeling")
commission_pct = st.sidebar.slider(
    "Commission Rate (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.01
)
slippage_pct = st.sidebar.slider(
    "Slippage (%)", min_value=0.0, max_value=1.0, value=0.05, step=0.01
)
run_button = st.sidebar.button("Run Backtest", type="primary", use_container_width=True)

if run_button:
    with st.spinner(f"Executing {strategy_type} on {ticker}..."):
        payload = bridge.execute_backtest(
            {
                "symbol": ticker,
                "capital": initial_capital,
                "commission": commission_pct,
                "slippage": slippage_pct,
                "strategy": strategy_type,
            }
        )

    st.success(f"Backtest completed for {ticker.upper()}")

    metrics = payload.metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Return", metrics.get("total_return", "0.00%"))
    col2.metric("Sharpe Ratio", metrics.get("sharpe_ratio", "0.00"))
    col3.metric("Max Drawdown", metrics.get("max_drawdown", "0.00%"))
    col4.metric("Win Rate", metrics.get("win_rate", "0.0%"))

    st.divider()

    tab_summary, tab_trades, tab_raw = st.tabs(
        ["Overview", "Trade Execution Log", "Raw Payload Data"]
    )

    with tab_summary:
        st.subheader("Performance Breakdown")
        summary_df = pd.DataFrame(list(metrics.items()), columns=["Metric", "Value"])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab_trades:
        st.subheader("Executed Trades")
        if payload.trades is not None and not payload.trades.empty:
            st.dataframe(payload.trades, use_container_width=True)
        else:
            st.info("No trades were executed during this backtest run.")

    with tab_raw:
        st.subheader("Bridge Payload Metadata")
        st.json(
            {
                "ticker": ticker,
                "strategy_type": strategy_type,
                "metrics": metrics,
                "logs": payload.logs,
            }
        )
else:
    st.info("Configure your backtest parameters in the sidebar and click Run Backtest to start backtesting.")