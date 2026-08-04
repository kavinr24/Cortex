import json

import pandas as pd
import streamlit as st
from bridge import CortexBridge

st.set_page_config(
    page_title="Cortex Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def get_bridge() -> CortexBridge:
    return CortexBridge()

bridge = get_bridge()

STRATEGY_MAP = {
    "SMA Crossover": "SMACrossover",
    "RSI Strategy": "RSIStrategy",
    "Bollinger Bands": "BollingerBandsStrategy",
    "MACD Strategy": "MACDStrategy",
    "EMA Crossover": "EMACrossover",
    "Stochastic Oscillator": "StochasticStrategy",
    "ATR Channel Breakout": "ATRStrategy",
}

st.title("Cortex Engine")

st.sidebar.header("Asset & Strategy Selection")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL")
selected_strategy_label = st.sidebar.selectbox(
    "Strategy Model",
    list(STRATEGY_MAP.keys()),
)
strategy_key = STRATEGY_MAP[selected_strategy_label]

st.sidebar.divider()
st.sidebar.header("Execution Window")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-01-01"))

st.sidebar.divider()
st.sidebar.header("Strategy Parameters")
strategy_params: dict[str, object] = {}

if strategy_key == "SMACrossover":
    strategy_params["fast_ema"] = st.sidebar.number_input(
        "Fast EMA Period", min_value=2, max_value=200, value=20
    )
    strategy_params["slow_ema"] = st.sidebar.number_input(
        "Slow EMA Period", min_value=5, max_value=500, value=50
    )
elif strategy_key == "RSIStrategy":
    strategy_params["rsi_period"] = st.sidebar.number_input(
        "RSI Period", min_value=2, max_value=100, value=14
    )
    strategy_params["oversold"] = st.sidebar.slider(
        "Oversold Threshold", min_value=10.0, max_value=45.0, value=30.0, step=1.0
    )
    strategy_params["overbought"] = st.sidebar.slider(
        "Overbought Threshold", min_value=55.0, max_value=90.0, value=70.0, step=1.0
    )
elif strategy_key == "BollingerBandsStrategy":
    strategy_params["period"] = st.sidebar.number_input(
        "MA Period", min_value=5, max_value=100, value=20
    )
    strategy_params["num_std"] = st.sidebar.number_input(
        "Std Dev Multiplier", min_value=0.5, max_value=4.0, value=2.0, step=0.1
    )
elif strategy_key == "MACDStrategy":
    strategy_params["fast_period"] = st.sidebar.number_input(
        "Fast Period", min_value=2, max_value=50, value=12
    )
    strategy_params["slow_period"] = st.sidebar.number_input(
        "Slow Period", min_value=5, max_value=100, value=26
    )
    strategy_params["signal_period"] = st.sidebar.number_input(
        "Signal Period", min_value=2, max_value=50, value=9
    )
elif strategy_key == "EMACrossover":
    strategy_params["fast_period"] = st.sidebar.number_input(
        "Fast Period", min_value=2, max_value=200, value=12
    )
    strategy_params["slow_period"] = st.sidebar.number_input(
        "Slow Period", min_value=5, max_value=500, value=26
    )
elif strategy_key == "StochasticStrategy":
    strategy_params["k_period"] = st.sidebar.number_input(
        "%K Period", min_value=2, max_value=50, value=14
    )
    strategy_params["d_period"] = st.sidebar.number_input(
        "%D Period", min_value=1, max_value=20, value=3
    )
    strategy_params["oversold"] = st.sidebar.slider(
        "Oversold Threshold", min_value=5.0, max_value=40.0, value=20.0, step=1.0
    )
    strategy_params["overbought"] = st.sidebar.slider(
        "Overbought Threshold", min_value=60.0, max_value=95.0, value=80.0, step=1.0
    )
elif strategy_key == "ATRStrategy":
    strategy_params["atr_period"] = st.sidebar.number_input(
        "ATR Period", min_value=2, max_value=100, value=14
    )
    strategy_params["atr_multiplier"] = st.sidebar.number_input(
        "ATR Multiplier", min_value=0.5, max_value=5.0, value=1.5, step=0.1
    )

st.sidebar.divider()
st.sidebar.header("Capital & Friction Settings")
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)", min_value=1000, value=100000, step=5000
)
commission_pct = st.sidebar.slider(
    "Commission Rate (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.01
)
slippage_pct = st.sidebar.slider(
    "Slippage (%)", min_value=0.0, max_value=1.0, value=0.05, step=0.01
)

run_button = st.sidebar.button("Run Backtest", type="primary", use_container_width=True)

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

        st.divider()

        tab_charts, tab_trades, tab_metrics, tab_raw = st.tabs(
            ["Performance Charts", "Trade History", "Detailed Metrics", "Export & Debug"]
        )

        with tab_charts:
            st.subheader("Performance Visualizations")
            if hasattr(payload, "equity_curve") and payload.equity_curve is not None and not payload.equity_curve.empty:
                st.markdown("**Equity Curve**")
                st.line_chart(payload.equity_curve[["Portfolio_Value"]])
            else:
                st.info("No equity curve data available for this run.")

        with tab_trades:
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

        with tab_metrics:
            st.subheader("Full Indicator Breakdown")
            metrics_df = pd.DataFrame(
                list(metrics.items()), columns=["Metric Indicator", "Calculated Value"]
            )
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)

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
