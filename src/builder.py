import logging
import operator
import pandas as pd
import numpy as np
from src.strategy import BaseStrategy

_LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")

COMPARISON_OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

CROSSOVER_COMPARISONS = ("cross_above", "crosses_above", "cross_below", "crosses_below")

VALID_COMPARISONS = tuple(sorted(COMPARISON_OPERATORS)) + CROSSOVER_COMPARISONS


def _canonical_comparison(comparison: str) -> str:
    comp = str(comparison).lower().strip()
    if comp == "cross_above":
        return "crosses_above"
    if comp == "cross_below":
        return "crosses_below"
    return comp


def validate_market_data(df: pd.DataFrame, required: tuple = REQUIRED_COLUMNS) -> None:
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected a pandas DataFrame, got {type(df).__name__}")
    if df.empty:
        raise ValueError("DataFrame is empty,  nothing to backtest.")
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")
    for col in required:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.isna().any():
            raise ValueError(f"Column '{col}' contains missing or non-numeric values.")


class CustomStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame):
        validate_market_data(df)
        super().__init__(df)
        self.entry_rules = []
        self.exit_rules = []

    def _validate_rule_args(self, left: str, comparison: str) -> str:
        if not isinstance(left, str):
            raise TypeError(f"Left side must be a column name, got {type(left).__name__}")
        if left not in self.df.columns:
            raise KeyError(f"Column not found: {left}")
        comp = _canonical_comparison(comparison)
        if comp not in VALID_COMPARISONS:
            raise ValueError(f"Invalid comparison: {comparison!r}. Valid options: {', '.join(VALID_COMPARISONS)}")
        return comp

    def add_entry_rule(self, left: str, comparison: str, right, logic: str = "AND"):
        comp = self._validate_rule_args(left, comparison)
        self.entry_rules.append((left, comp, right, logic.upper()))
        return self

    def add_exit_rule(self, left: str, comparison: str, right, logic: str = "AND"):
        comp = self._validate_rule_args(left, comparison)
        self.exit_rules.append((left, comp, right, logic.upper()))
        return self

    def add_entry(self, left: str, comparison: str, right, logic: str = "AND"):
        return self.add_entry_rule(left, comparison, right, logic)

    def add_exit(self, left: str, comparison: str, right, logic: str = "AND"):
        return self.add_exit_rule(left, comparison, right, logic)

    def _get_value(self, value):
        # if value is a column name, return the aligned, numeric-coerced series
        if isinstance(value, str):
            if value in self.df.columns:
                return pd.to_numeric(self.df[value], errors="coerce").reindex(self.df.index)
            # try to parse numeric literal from string
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"Right value must be a column name or numeric literal: {value!r}")
            if not np.isfinite(parsed):
                raise ValueError(f"Right value must be finite, got {value!r}")
            return parsed

        # if it's a pandas Series, align index to self.df and coerce numeric
        if isinstance(value, pd.Series):
            return pd.to_numeric(value, errors="coerce").reindex(self.df.index)

        # otherwise treat as numeric scalar
        numeric = pd.to_numeric(value, errors="coerce")
        if pd.isna(numeric) or not np.isfinite(float(numeric)):
            raise ValueError(f"Right-hand value must be a finite number, got {value!r}")
        return float(numeric)

    def _check_condition(self, condition):
        left_name, comparison, right_value, _ = condition
        comparison = str(comparison).lower().strip()
        if left_name not in self.df.columns:
            raise KeyError(f"Column not found: {left_name}")

        left = pd.to_numeric(self.df[left_name], errors="coerce")
        right = self._get_value(right_value)

        if left.isna().all():
            return pd.Series(False, index=self.df.index)

        # handle crossover comparisons (support both singular and plural forms)
        if comparison in ("cross_above", "crosses_above"):
            if isinstance(right, pd.Series):
                right_curr = right.reindex(self.df.index)
                right_prev = right.shift(1)
            else:
                right_curr = right
                right_prev = right
            result = (left > right_curr) & (left.shift(1) <= right_prev)
        elif comparison in ("cross_below", "crosses_below"):
            if isinstance(right, pd.Series):
                right_curr = right.reindex(self.df.index)
                right_prev = right.shift(1)
            else:
                right_curr = right
                right_prev = right
            result = (left < right_curr) & (left.shift(1) >= right_prev)
        else:
            if comparison not in COMPARISON_OPERATORS:
                raise ValueError(f"Invalid comparison: {comparison}")
            result = COMPARISON_OPERATORS[comparison](left, right)

        return result.fillna(False)

    def _combine_rules(self, rules):
        if not rules:
            return pd.Series(False, index=self.df.index)
        mask = self._check_condition(rules[0])

        for condition in rules[1:]:
            current_mask = self._check_condition(condition)
            logic = condition[3]

            if logic == "OR":
                mask = mask | current_mask
            else:
                mask = mask & current_mask

        # ensure boolean dtype and same index
        mask = mask.reindex(self.df.index).fillna(False).astype(bool)
        return mask

    def generate_signals(self) -> pd.DataFrame:
        validate_market_data(self.df)

        # evaluate entry and exit rules
        entry_signal = self._combine_rules(self.entry_rules)
        exit_signal = self._combine_rules(self.exit_rules)

        # log mask statistics for debugging
        try:
            _LOGGER.info("entry_mask_true=%d exit_mask_true=%d", int(entry_signal.sum()), int(exit_signal.sum()))
        except Exception:
            pass

        # exit signals take priority if entry and exit triggered on the same row
        entry_signal = entry_signal & (~exit_signal)

        # build integer signal series aligned to df index
        signal_series = pd.Series(0, index=self.df.index, dtype=int)
        signal_series.loc[entry_signal] = 1
        signal_series.loc[exit_signal] = -1

        # store helper columns for inspection
        self.df["entry_signal"] = entry_signal.astype(bool)
        self.df["exit_signal"] = exit_signal.astype(bool)

        # final signal and position change
        self.df["signal"] = signal_series
        self.df["position_change"] = self.df["signal"].diff().fillna(0)

        return self.df
