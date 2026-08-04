import pandas as pd
import streamlit as st


STRATEGY_MAP = {
    "SMA Crossover": "SMACrossover",
    "RSI Strategy": "RSIStrategy",
    "Bollinger Bands": "BollingerBandsStrategy",
    "MACD Strategy": "MACDStrategy",
    "EMA Crossover": "EMACrossover",
    "Stochastic Oscillator": "StochasticStrategy",
    "ATR Channel Breakout": "ATRStrategy",
}


def render_sidebar():
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

    return (
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
    )
