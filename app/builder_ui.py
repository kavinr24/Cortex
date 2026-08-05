import uuid
from typing import Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

from src.backtester import Backtester
from src.builder import CustomStrategy

from charts import render_performance_chart
from metrics import render_summary_metrics

REQUIRED_COLUMNS = {"open", "high", "low", "close", "volume"}

_COMPARISON_OPTIONS = [">", ">=", "<", "<=", "==", "!=", "crosses_above", "crosses_below"]


def _new_rule_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def init_builder_state() -> None:
    if "entry_rules" not in st.session_state:
        st.session_state.entry_rules = []
    if "exit_rules" not in st.session_state:
        st.session_state.exit_rules = []
    if "last_backtest" not in st.session_state:
        st.session_state.last_backtest = None


def render_rule_inputs(rule_type: str, available_columns: list) -> None:
    rules_key = f"{rule_type}_rules"

    st.subheader(f"{rule_type.capitalize()} Rules")

    # make sure key exists
    if rules_key not in st.session_state:
        st.session_state[rules_key] = []

    rules_to_delete = []

    for idx, rule in enumerate(list(st.session_state[rules_key])):
        # drop malformed  entries instead of crashing
        if not isinstance(rule, dict):
            rules_to_delete.append(idx)
            continue

        if not rule.get("id"):
            rule["id"] = _new_rule_id(rules_key)
        rule_id = rule["id"]

        # adjusted column ratios for tighter layout
        col1, col2, col3, col4, col5 = st.columns([2.2, 1.8, 3.0, 1.5, 1.2])

        with col1:
            try:
                left_index = available_columns.index(rule.get("left"))
            except Exception:
                left_index = 0
            left = st.selectbox(
                "Indicator",
                options=available_columns,
                index=left_index,
                key=f"{rules_key}_left_{rule_id}",
            )

        with col2:
            try:
                comp_index = _COMPARISON_OPTIONS.index(rule.get("comparison"))
            except Exception:
                comp_index = 0
            comp = st.selectbox(
                "Condition",
                options=_COMPARISON_OPTIONS,
                index=comp_index,
                key=f"{rules_key}_comp_{rule_id}",
            )

        with col3:
            # find if right is a column or scalar
            right_is_column = isinstance(rule.get("right"), str) and rule.get("right") in available_columns
            type_index = 0 if right_is_column else 1
            val_type = st.selectbox(
                "Type",
                options=["Column", "Scalar"],
                index=type_index,
                key=f"{rules_key}_type_{rule_id}",
            )

            if val_type == "Column":
                try:
                    right_index = available_columns.index(rule.get("right"))
                except Exception:
                    right_index = 0
                right = st.selectbox(
                    "Compare To",
                    options=available_columns,
                    index=right_index,
                    key=f"{rules_key}_right_col_{rule_id}",
                )
            else:
                try:
                    default_val = float(rule.get("right", 0.0))
                    if not np.isfinite(default_val):
                        default_val = 0.0
                except Exception:
                    default_val = 0.0
                right = st.number_input(
                    "Value",
                    value=default_val,
                    key=f"{rules_key}_right_val_{rule_id}",
                    label_visibility="collapsed",
                )

        with col4:
            logic = st.selectbox(
                "Logic",
                options=["AND", "OR"],
                index=0 if rule.get("logic", "AND") == "AND" else 1,
                key=f"{rules_key}_logic_{rule_id}",
            )

        with col5:
            # vertically center the delete button
            container = col5.container()
            container.markdown(
                "<div style='display:flex;align-items:center;height:100%'>",
                unsafe_allow_html=True,
            )
            if container.button("Delete", key=f"{rules_key}_del_{rule_id}"):
                rules_to_delete.append(idx)
            container.markdown("</div>", unsafe_allow_html=True)

        # update the rule in session state in place
        rule["left"] = left
        rule["comparison"] = comp
        rule["right"] = right
        rule["logic"] = logic

    # remove deleted rules in reverse order, then rerun once
    for idx in sorted(rules_to_delete, reverse=True):
        st.session_state[rules_key].pop(idx)
    if rules_to_delete:
        st.rerun()

    if st.button(f"Add {rule_type.capitalize()} Rule", key=f"add_{rules_key}"):
        default_left = available_columns[0] if available_columns else ""
        st.session_state[rules_key].append({
            "id": _new_rule_id(rules_key),
            "left": default_left,
            "comparison": ">",
            "right": 0.0,
            "logic": "AND",
        })
        st.rerun()


def _build_and_run(df: pd.DataFrame, settings: Dict) -> Optional[Dict]:
    strategy = CustomStrategy(df)

    for rule in st.session_state.entry_rules:
        strategy.add_entry_rule(
            left=rule["left"],
            comparison=rule["comparison"],
            right=rule["right"],
            logic=rule.get("logic", "AND"),
        )

    for rule in st.session_state.exit_rules:
        strategy.add_exit_rule(
            left=rule["left"],
            comparison=rule["comparison"],
            right=rule["right"],
            logic=rule.get("logic", "AND"),
        )

    result_df = strategy.generate_signals()

    bt = Backtester(
        initial_capital=float(settings["initial_capital"]),
        commission_rate=float(settings["commission_pct"]) / 100.0,
        slippage_rate=float(settings["slippage_pct"]) / 100.0,
    )

    bt_df = bt.run(result_df.copy())

    # ensure compatibility with chart renderer
    if "total_equity" in bt_df.columns:
        bt_df["Portfolio_Value"] = bt_df["total_equity"]

    # compute summary metrics with NaN/empty guards
    initial = float(bt.initial_capital)
    final_balance = float(bt_df["total_equity"].iloc[-1]) if not bt_df.empty else 0.0
    total_return_pct = (final_balance - initial) / initial * 100.0 if initial > 0 else 0.0

    returns = bt_df.get("returns")
    if returns is None or returns.empty:
        returns = bt_df["total_equity"].pct_change().fillna(0.0)

    std = returns.std()
    if len(returns) > 1 and std is not None and not np.isnan(std) and std != 0:
        sharpe = float((returns.mean() / std * np.sqrt(252)))
    else:
        sharpe = 0.0

    rolling_max = bt_df["total_equity"].cummax().replace(0, np.nan)
    drawdown = (bt_df["total_equity"] - rolling_max) / rolling_max
    drawdown = drawdown.fillna(0.0)
    max_dd = float(drawdown.min() * 100.0) if not drawdown.empty else 0.0

    trades_df = bt.get_trade_log()
    win_rate = 0.0
    if not trades_df.empty and "pnl" in trades_df.columns:
        win_rate = float((trades_df["pnl"] > 0).sum() / len(trades_df) * 100.0)

    metrics = {
        "total_return": f"{total_return_pct:+.2f}%",
        "final_balance": f"${final_balance:,.2f}",
        "net_pnl": f"${(final_balance - initial):,.2f}",
        "max_drawdown": f"{max_dd:.2f}%",
        "sharpe_ratio": f"{sharpe:.2f}",
        "win_rate": f"{win_rate:.1f}%",
        "total_trades": len(trades_df),
    }

    return {
        "result_df": result_df,
        "bt_df": bt_df,
        "metrics": metrics,
        "trades_df": trades_df,
    }


def _render_backtest_results(payload: Dict) -> None:
    st.subheader("Backtest Results")
    render_summary_metrics(payload["metrics"])

    # simple payload object for chart renderer
    class _P:
        pass

    chart_payload = _P()
    chart_payload.equity_curve = payload["bt_df"]
    chart_payload.metrics = payload["metrics"]

    render_performance_chart(chart_payload)

    st.subheader("Trade Log")
    trades_df = payload["trades_df"]
    if trades_df.empty:
        st.info("No trades were generated by this strategy.")
    else:
        st.dataframe(trades_df)


def render_strategy_builder(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    init_builder_state()

    st.header("Strategy Builder")

    if not isinstance(df, pd.DataFrame) or df is None or df.empty:
        st.error("No valid market data available to build a strategy.")
        return None

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"Market data is missing required columns: {', '.join(missing)}")
        return None

    # only include numeric columns as selectable indicators (exclude timestamps)
    available_columns = [
        col
        for col in df.columns
        if col not in ["signal", "position_change"] and pd.api.types.is_numeric_dtype(df[col])
    ]

    if not available_columns:
        st.error("No valid columns found in dataframe.")
        return None

    col_entry, col_exit = st.columns(2)

    with col_entry:
        render_rule_inputs("entry", available_columns)

    with col_exit:
        render_rule_inputs("exit", available_columns)

    st.markdown("---")

    # always rendered settings keep widget state stable durig reruns
    with st.expander("Backtest Settings", expanded=False):
        initial_capital = st.number_input("Initial Capital ($)", min_value=1.0, value=100000.0, step=1000.0)
        commission_pct = st.number_input("Commission (%)", min_value=0.0, max_value=100.0, value=0.1, step=0.01)
        slippage_pct = st.number_input("Slippage (%)", min_value=0.0, max_value=100.0, value=0.05, step=0.01)

    settings = {
        "initial_capital": initial_capital,
        "commission_pct": commission_pct,
        "slippage_pct": slippage_pct,
    }

    if st.button("Apply Strategy", type="primary"):
        if not st.session_state.entry_rules and not st.session_state.exit_rules:
            st.warning("Add at least one entry or exit rule before applying the strategy.")
            return None

        try:
            st.session_state.last_backtest = _build_and_run(df, settings)
        except Exception as e:
            st.error(f"Backtest failed: {e}")
            return None

    # render last successful results, if any
    last = st.session_state.last_backtest
    if last is not None:
        _render_backtest_results(last)
        return last["result_df"]

    return None
