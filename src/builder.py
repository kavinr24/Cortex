import operator
import pandas as pd
import numpy as np
from src.strategy import BaseStrategy

class CustomStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame):
        super().__init__(df)
        self.entry_rules = []
        self.exit_rules = []

    def add_entry_rule(self, left: str, comparison: str, right, logic: str = "AND"):
        self.entry_rules.append((left, comparison, right, logic.upper()))
        return self

    def add_exit_rule(self, left: str, comparison: str, right, logic: str = "AND"):
        self.exit_rules.append((left, comparison, right, logic.upper()))
        return self

    def add_entry(self, left: str, comparison: str, right, logic: str = "AND"):
        return self.add_entry_rule(left, comparison, right, logic)

    def add_exit(self, left: str, comparison: str, right, logic: str = "AND"):
        return self.add_exit_rule(left, comparison, right, logic)

    def _get_value(self, value):
        if isinstance(value, str):
            if value not in self.df.columns:
                raise KeyError(f"Column not found: {value}")
            return self.df[value]
        return value

    def _check_condition(self, condition):
        left_name, comparison, right_value, _ = condition
        if left_name not in self.df.columns:
            raise KeyError(f"Column not found: {left_name}")

        left = self.df[left_name]
        right = self._get_value(right_value)

        if comparison in ["cross_above", "crosses_above"]:
            previous_right = right.shift(1) if isinstance(right, pd.Series) else right
            result = (left > right) & (left.shift(1) <= previous_right)
        elif comparison in ["cross_below", "crosses_below"]:
            previous_right = right.shift(1) if isinstance(right, pd.Series) else right
            result = (left < right) & (left.shift(1) >= previous_right)
        else:
            comparisons = {
                ">": operator.gt,
                ">=": operator.ge,
                "<": operator.lt,
                "<=": operator.le,
                "==": operator.eq,
                "!=": operator.ne,
            }
            if comparison not in comparisons:
                raise ValueError(f"Invalid comparison: {comparison}")
            result = comparisons[comparison](left, right)

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

        return mask

    def generate_signals(self) -> pd.DataFrame:
        # evaluate entry and exit rules
        entry_signal = self._combine_rules(self.entry_rules)
        exit_signal = self._combine_rules(self.exit_rules)

        # exit signals take priority if entry and exit triggered on the same row
        entry_signal = entry_signal & (~exit_signal)

        signals = np.zeros(len(self.df))
        signals[entry_signal] = 1
        signals[exit_signal] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff().fillna(0)

        return self.df

