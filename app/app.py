from pathlib import Path
import sys

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge import CortexBridge

st.set_page_config(
    page_title="Cortex Backtester",
    layout="wide"
)

st.title("Cortex Dashboard")
st.write("Initializing UI and connecting to backend...")

bridge = CortexBridge()

st.sidebar.header("Backtest Configuration")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL")

if st.sidebar.button("Run Backtest"):
    with st.spinner("Running strategy..."):
        payload = bridge.execute_backtest({"symbol": ticker})

        st.success("Backtest executed successfully!")
        st.json(payload.metrics)
        if payload.logs:
            st.text_area("Logs", value="\n".join(payload.logs), height=200)
