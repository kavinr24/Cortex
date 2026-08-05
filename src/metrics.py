import numpy as np
import pandas as pd
from typing import Any, Dict, Optional, cast


class PerformanceMetrics:
    # evals backtest results with return, risk, drawdown, and trade stats

    def __init__(
        self,
        backtest_df: pd.DataFrame,
        trade_log: Optional[pd.DataFrame] = None,
        risk_free_rate: float = 0.02,
        initial_capital: float = 100000.0,
    ):
        self.raw_df = backtest_df.copy()
        self.risk_free_rate = float(risk_free_rate)
        self.initial_capital = float(initial_capital) if initial_capital and np.isfinite(initial_capital) else 0.0
        self.daily_rf = (1 + self.risk_free_rate) ** (1 / 252) - 1

        self.df = self._preprocess()

        if trade_log is not None and not trade_log.empty:
            self.trade_log = trade_log.copy()
        else:
            self.trade_log = pd.DataFrame()

    # input validation and preprocesssing

    def _preprocess(self) -> pd.DataFrame:
        # cleans the backtest df and computes return series
        df = self.raw_df.copy()

        if "total_equity" not in df.columns:
            return pd.DataFrame()

        df = df.dropna(subset=["total_equity"])
        df = df[np.isfinite(pd.to_numeric(df["total_equity"], errors="coerce"))]
        df = df.reset_index(drop=True)

        if df.empty:
            return df

        df["returns"] = df["returns"].fillna(0.0)
        df["daily_return"] = df["total_equity"].pct_change().fillna(0.0)
        df["log_return"] = np.log1p(df["daily_return"])
        df["cumulative_return"] = (df["total_equity"] / self.initial_capital) - 1.0 if self.initial_capital > 0 else 0.0
        df["excess_return"] = df["daily_return"] - self.daily_rf

        return df

    # return metrics

    def _total_return(self) -> float:
        # % change from inital to final equity
        if self.df.empty or self.initial_capital <= 0:
            return 0.0

        final_equity = float(self.df["total_equity"].iloc[-1])
        if not np.isfinite(final_equity):
            return 0.0
        return ((final_equity / self.initial_capital) - 1.0) * 100

    def _cagr(self) -> float:
        # compound annaul growth rate of the portfolio
        # CAGR = (final / initial) ^ (1 / years) - 1
        if self.df.empty:
            return 0.0

        final_equity = float(self.df["total_equity"].iloc[-1])
        total_days = len(self.df)

        # avoid division by zero if less than 1 trading day
        if total_days <= 1:
            return 0.0

        years = total_days / 252
        if self.initial_capital <= 0 or final_equity <= 0 or not np.isfinite(final_equity):
            return 0.0

        cagr = (final_equity / self.initial_capital) ** (1 / years) - 1.0
        return cagr * 100

    def _annualized_volatility(self) -> float:
        # annualized vol of daily returns
        # daily std * sqrt(252) gives annualized vol
        if self.df.empty:
            return 0.0

        daily_std = self.df["daily_return"].std()
        if daily_std == 0 or pd.isna(daily_std) or not np.isfinite(daily_std):
            return 0.0
        return daily_std * np.sqrt(252) * 100

    # risk adjust ratos

    def _sharpe_ratio(self) -> float:
        # Sharpe = mean(excess_return) / std(excess_return) * sqrt(252)
        if self.df.empty:
            return 0.0

        excess = self.df["excess_return"]
        if excess.empty:
            return 0.0

        mean = float(excess.mean())
        std = float(excess.std())

        if std == 0 or not np.isfinite(std) or not np.isfinite(mean):
            return 0.0

        sharpe = (mean / std) * np.sqrt(252)
        return sharpe

    def _sortino_ratio(self) -> float:
        # Sortino = mean(excess_return) / downside_deviation * sqrt(252)
        if self.df.empty:
            return 0.0

        downside = self.df["daily_return"] - self.daily_rf
        downside_std = downside[downside < 0].std()

        if downside_std == 0 or pd.isna(downside_std) or not np.isfinite(downside_std):
            return 0.0

        mean = float(self.df["daily_return"].mean())
        if not np.isfinite(mean):
            return 0.0

        sortino = (mean - self.daily_rf) / downside_std * np.sqrt(252)
        return sortino

    def _calmar_ratio(self) -> float:
        # calmar = cagr/max drawdown (abs)
        max_dd = abs(self._max_drawdown())
        if max_dd == 0 or not np.isfinite(max_dd):
            return 0.0

        return self._cagr() / max_dd

    def _closed_trades(self) -> pd.DataFrame:
        # return all closed trades
        if self.trade_log.empty or "status" not in self.trade_log.columns:
            return pd.DataFrame()
        return cast(pd.DataFrame, self.trade_log[self.trade_log["status"] == "CLOSED"])

    def _profit_factor(self) -> float:
        # gross profits/losses form log
        closed = self._closed_trades()
        if closed.empty or "pnl" not in closed.columns:
            return 0.0

        gross_profits = closed.loc[closed["pnl"] > 0, "pnl"].sum()
        gross_losses = abs(closed.loc[closed["pnl"] < 0, "pnl"].sum())

        if not np.isfinite(gross_profits) or not np.isfinite(gross_losses):
            return 0.0

        if gross_losses == 0:
            return float("inf") if gross_profits > 0 else 0.0

        return gross_profits / gross_losses

    # DRAWDOWN ANALYSIS

    def _high_water_mark(self) -> pd.Series:
        # running max of total equity
        # cummax tracks the highest equity seen so far
        return cast(pd.Series, self.df["total_equity"].cummax())

    def _drawdown_series(self) -> pd.Series:
        # % decline from high water mark at each point
        hwm = self._high_water_mark()
        # guard against division by zero when equity/hwm is 0
        safe_hwm = hwm.mask(hwm <= 0, np.nan)
        drawdown = (self.df["total_equity"] - safe_hwm) / safe_hwm * 100
        return cast(pd.Series, drawdown.fillna(0.0))

    def _max_drawdown(self) -> float:
        # max drawdown %
        if self.df.empty:
            return 0.0
        dd = self._drawdown_series()
        if dd.empty:
            return 0.0
        return float(dd.min()) if np.isfinite(float(dd.min())) else 0.0

    def _max_drawdown_duration(self) -> int:
        # longest streak of days in drawdown
        if self.df.empty:
            return 0
        # longest streak of days in drawdown
        hwm = self._high_water_mark()
        in_drawdown = self.df["total_equity"] < hwm
        return self._max_consecutive(in_drawdown)

    # PERFORMANCE STATS

    def _trade_stats(self) -> Dict[str, Any]:
        # compute all stats from the log
        defaults: Dict[str, Any] = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "avg_trade_gain": 0.0,
            "avg_trade_loss": 0.0,
            "win_loss_ratio": 0.0,
            "best_trade_pnl": 0.0,
            "best_trade_pnl_pct": 0.0,
            "worst_trade_pnl": 0.0,
            "worst_trade_pnl_pct": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "avg_holding_period_days": 0.0,
        }

        closed = self._closed_trades()
        if closed.empty or "pnl" not in closed.columns:
            return defaults

        stats = defaults.copy()

        pnl = pd.to_numeric(closed["pnl"], errors="coerce")
        pnl_pct = (
            pd.to_numeric(closed["pnl_pct"], errors="coerce") * 100
            if "pnl_pct" in closed.columns
            else pd.Series(np.nan, index=closed.index)
        )

        # winning vs losing trades
        winners = pnl > 0
        losers = pnl < 0

        stats["total_trades"] = int(len(closed))
        stats["winning_trades"] = int(winners.sum())
        stats["losing_trades"] = int(losers.sum())

        # win rate percentage
        if stats["total_trades"] > 0:
            stats["win_rate"] = (stats["winning_trades"] / stats["total_trades"]) * 100

        # average trade gain and loss
        stats["avg_trade_gain"] = float(pnl[winners].mean()) if winners.any() else 0.0
        stats["avg_trade_loss"] = float(pnl[losers].mean()) if losers.any() else 0.0

        # win/loss ratio (average win / average loss)
        if stats["avg_trade_loss"] not in (0.0, None) and np.isfinite(stats["avg_trade_loss"]):
            stats["win_loss_ratio"] = abs(stats["avg_trade_gain"] / stats["avg_trade_loss"])

        # best and worst single trade
        if not pnl.empty:
            stats["best_trade_pnl"] = float(pnl.max()) if np.isfinite(float(pnl.max())) else 0.0
            stats["worst_trade_pnl"] = float(pnl.min()) if np.isfinite(float(pnl.min())) else 0.0
        if not pnl_pct.dropna().empty:
            stats["best_trade_pnl_pct"] = float(pnl_pct.max()) if np.isfinite(float(pnl_pct.max())) else 0.0
            stats["worst_trade_pnl_pct"] = float(pnl_pct.min()) if np.isfinite(float(pnl_pct.min())) else 0.0

        # max consecutive wins and losses
        stats["max_consecutive_wins"] = self._max_consecutive(pnl > 0)
        stats["max_consecutive_losses"] = self._max_consecutive(pnl < 0)

        # average holding period in days
        stats["avg_holding_period_days"] = self._avg_holding_period(closed)

        return stats

    @staticmethod
    def _max_consecutive(mask: pd.Series) -> int:
        # longest streak of True values in a series
        max_streak = 0
        current_streak = 0

        for val in mask.fillna(False):
            if val:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
            else:
                current_streak = 0

        return max_streak

    def _avg_holding_period(self, closed_trades: pd.DataFrame) -> float:
        # avg number of days between entry and exit
        if "entry_date" not in closed_trades.columns or "exit_date" not in closed_trades.columns:
            return 0.0

        # convert date strings to datetime, coercing errors to NaT
        entry = pd.to_datetime(closed_trades["entry_date"], errors="coerce")
        exit_ = pd.to_datetime(closed_trades["exit_date"], errors="coerce")
        valid = entry.notna() & exit_.notna()
        if valid.sum() == 0:
            return 0.0

        duration = cast(pd.Series, exit_[valid] - entry[valid])
        holding_days = duration.dt.total_seconds() / 86400
        return float(holding_days.mean())

    # formatting and display

    def calculate_all(self) -> Dict[str, float]:
        # return a flat dict with metrics rounded to 4 decimals
        trade_stats = self._trade_stats()

        metrics: Dict[str, float] = {
            # --- Return Metrics ---
            "Total Return (%)": self._total_return(),
            "CAGR (%)": self._cagr(),
            "Annualized Volatility (%)": self._annualized_volatility(),
            # --- Risk-Adjusted Ratios ---
            "Sharpe Ratio": self._sharpe_ratio(),
            "Sortino Ratio": self._sortino_ratio(),
            "Calmar Ratio": self._calmar_ratio(),
            "Profit Factor": self._profit_factor(),
            # --- Drawdown Analysis ---
            "Max Drawdown (%)": self._max_drawdown(),
            "Max Drawdown Duration (days)": self._max_drawdown_duration(),
            # --- Trade Statistics ---
            "Total Trades": trade_stats["total_trades"],
            "Winning Trades": trade_stats["winning_trades"],
            "Losing Trades": trade_stats["losing_trades"],
            "Win Rate (%)": trade_stats["win_rate"],
            "Avg Trade Gain ($)": trade_stats["avg_trade_gain"],
            "Avg Trade Loss ($)": trade_stats["avg_trade_loss"],
            "Win/Loss Ratio": trade_stats["win_loss_ratio"],
            "Best Trade PnL ($)": trade_stats["best_trade_pnl"],
            "Best Trade PnL (%)": trade_stats["best_trade_pnl_pct"],
            "Worst Trade PnL ($)": trade_stats["worst_trade_pnl"],
            "Worst Trade PnL (%)": trade_stats["worst_trade_pnl_pct"],
            "Max Consecutive Wins": trade_stats["max_consecutive_wins"],
            "Max Consecutive Losses": trade_stats["max_consecutive_losses"],
            "Avg Holding Period (days)": trade_stats["avg_holding_period_days"],
        }

        # sanitize any remaining non-finite values
        cleaned: Dict[str, float] = {}
        for key, value in metrics.items():
            try:
                value = float(value)
                if not np.isfinite(value):
                    value = 0.0
            except (TypeError, ValueError):
                value = 0.0
            cleaned[key] = round(value, 4)
        return cleaned

    def to_dataframe(self) -> pd.DataFrame:
        metrics = self.calculate_all()
        df = pd.DataFrame(list(metrics.items()), columns=["Metric", "Value"])
        return df

    def summary(self) -> None:
        metrics = self.calculate_all()

        # define section groupings for organized display
        sections = {
            "RETURN METRICS": [
                "Total Return (%)",
                "CAGR (%)",
                "Annualized Volatility (%)",
            ],
            "RISK-ADJUSTED RATIOS": [
                "Sharpe Ratio",
                "Sortino Ratio",
                "Calmar Ratio",
                "Profit Factor",
            ],
            "DRAWDOWN ANALYSIS": [
                "Max Drawdown (%)",
                "Max Drawdown Duration (days)",
            ],
            "TRADE STATISTICS": [
                "Total Trades",
                "Winning Trades",
                "Losing Trades",
                "Win Rate (%)",
                "Avg Trade Gain ($)",
                "Avg Trade Loss ($)",
                "Win/Loss Ratio",
                "Best Trade PnL ($)",
                "Best Trade PnL (%)",
                "Worst Trade PnL ($)",
                "Worst Trade PnL (%)",
                "Max Consecutive Wins",
                "Max Consecutive Losses",
                "Avg Holding Period (days)",
            ],
        }

        # print the header
        print("=" * 50)
        print("        PERFORMANCE SUMMARY")
        print("=" * 50)

        # print each section with its metrics
        for section_name, keys in sections.items():
            print(f"\n  {section_name}")
            print("  " + "-" * (len(section_name) + 2))
            for key in keys:
                val = metrics.get(key, 0.0)
                # right-align the value for clean columns
                print(f"    {key:<35} {val:>15}")

        print("\n" + "=" * 50)
