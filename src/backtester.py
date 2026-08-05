from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from src.builder import validate_market_data


@dataclass
class Trade:
    ticker: str
    entry_date: str
    exit_date: Optional[str] = None
    direction: int = 1  # 1 for Long, -1 for Short
    entry_price: float = 0.0
    exit_price: float = 0.0
    shares: float = 0.0
    commission: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = "OPEN"  # OPEN or CLOSED
    exit_reason: str = "SIGNAL"  # SIGNAL, STOP_LOSS, TAKE_PROFIT, END_OF_DATA


def _clamp(value: float, low: float, high: float, name: str) -> float:
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return min(max(value, low), high)


class Backtester:
    # simulates a backtest with slippage, commission, stop loss and tp

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        position_size_pct: float = 0.95,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
    ):
        initial_capital = float(initial_capital)
        if not np.isfinite(initial_capital) or initial_capital <= 0:
            raise ValueError(f"initial_capital must be a positive finite number, got {initial_capital!r}")

        self.initial_capital = initial_capital
        self.commission_rate = _clamp(commission_rate, 0.0, 0.99, "commission_rate")
        self.slippage_rate = _clamp(slippage_rate, 0.0, 0.99, "slippage_rate")
        self.position_size_pct = _clamp(position_size_pct, 0.0, 1.0, "position_size_pct")
        self.stop_loss_pct = _clamp(stop_loss_pct, 0.0, 0.99, "stop_loss_pct") if stop_loss_pct is not None else None
        self.take_profit_pct = _clamp(take_profit_pct, 0.0, 0.99, "take_profit_pct") if take_profit_pct is not None else None
        self.trades: List[Trade] = []

    def calculate_adjusted_entry_price(self, close_price: float) -> float:
        return close_price * (1 + self.slippage_rate)

    def calculate_adjusted_exit_price(self, exit_price: float) -> float:
        return exit_price * (1 - self.slippage_rate)

    def calculate_commission(self, total_value: float) -> float:
        return total_value * self.commission_rate

    def calculate_position_size(self, cash: float, entry_price: float) -> float:
        if not np.isfinite(cash) or not np.isfinite(entry_price) or entry_price <= 0:
            return 0.0
        allocated_cash = cash * self.position_size_pct
        return allocated_cash / entry_price

    def check_stop_loss(self, entry_price: float, low_price: float) -> bool:
        if self.stop_loss_pct is None:
            return False
        stop_price = entry_price * (1 - self.stop_loss_pct)
        return low_price <= stop_price

    def check_take_profit(self, entry_price: float, high_price: float) -> bool:
        if self.take_profit_pct is None:
            return False
        target_price = entry_price * (1 + self.take_profit_pct)
        return high_price >= target_price

    def check_risk_management(
        self, trade: Trade, high_price: float, low_price: float
    ) -> Tuple[Optional[float], Optional[str]]:
        if trade.direction == 1:
            if self.check_stop_loss(trade.entry_price, low_price):
                stop_price = trade.entry_price * (1 - self.stop_loss_pct)
                return stop_price, "STOP_LOSS"

            if self.check_take_profit(trade.entry_price, high_price):
                target_price = trade.entry_price * (1 + self.take_profit_pct)
                return target_price, "TAKE_PROFIT"

        return None, None

    def execute_long_entry(
        self, cash: float, close_price: float, ticker: str, current_date: str
    ) -> Tuple[float, float, Optional[Trade]]:
        entry_price_adj = self.calculate_adjusted_entry_price(close_price)
        shares_to_buy = self.calculate_position_size(cash, entry_price_adj)

        if shares_to_buy <= 0:
            return cash, 0.0, None

        cost_basis = shares_to_buy * entry_price_adj
        commission = self.calculate_commission(cost_basis)
        total_cost = cost_basis + commission

        if not np.isfinite(total_cost) or cash < total_cost:
            return cash, 0.0, None

        remaining_cash = cash - total_cost

        new_trade = Trade(
            ticker=ticker,
            entry_date=current_date,
            direction=1,
            entry_price=entry_price_adj,
            shares=shares_to_buy,
            commission=commission,
            status="OPEN",
        )

        return remaining_cash, shares_to_buy, new_trade

    def execute_exit(
        self,
        cash: float,
        shares: float,
        exit_price: float,
        current_date: str,
        trade: Trade,
        reason: str,
    ) -> float:
        exit_price_adj = self.calculate_adjusted_exit_price(exit_price)
        gross_proceeds = shares * exit_price_adj
        commission_exit = self.calculate_commission(gross_proceeds)
        net_proceeds = gross_proceeds - commission_exit

        new_cash = cash + net_proceeds

        # update trade tracking object
        trade.exit_date = current_date
        trade.exit_price = exit_price_adj
        trade.commission += commission_exit

        cost_basis = trade.entry_price * trade.shares
        if trade.entry_price > 0 and cost_basis > 0 and np.isfinite(cost_basis):
            trade.pnl = (exit_price_adj - trade.entry_price) * trade.shares - trade.commission
            trade.pnl_pct = trade.pnl / cost_basis

        trade.status = "CLOSED"
        trade.exit_reason = reason

        return new_cash

    def run(self, df: pd.DataFrame, ticker: str = "ASSET") -> pd.DataFrame:
        validate_market_data(df)
        data = df.copy().reset_index(drop=True)

        # snapshot required columns into contiguous numpy arrays for a fast loop
        close_arr = pd.to_numeric(data["close"], errors="coerce").to_numpy(dtype=float)
        has_high_low = "high" in data.columns and "low" in data.columns
        high_arr = pd.to_numeric(data["high"], errors="coerce").to_numpy(dtype=float) if has_high_low else close_arr
        low_arr = pd.to_numeric(data["low"], errors="coerce").to_numpy(dtype=float) if has_high_low else close_arr
        timestamp_arr = data["timestamp"].astype(str).to_numpy() if "timestamp" in data.columns else None

        # ensure signal column exists and has no NaNs
        if "signal" in data.columns:
            signal_arr = pd.to_numeric(data["signal"], errors="coerce").fillna(0).astype(int).to_numpy()
        else:
            signal_arr = np.zeros(len(data), dtype=int)

        n = len(data)
        cash_arr = np.empty(n)
        holdings_arr = np.empty(n)
        equity_arr = np.empty(n)
        shares_arr = np.empty(n)

        cash = float(self.initial_capital)
        shares = 0.0
        self.trades = []
        active_trade: Optional[Trade] = None

        # main simulation loop (signals generated at t are acted on at t+1)
        for i in range(n):
            current_date = str(timestamp_arr[i]) if timestamp_arr is not None else str(i)
            close_price = float(close_arr[i])
            high_price = float(high_arr[i]) if has_high_low else close_price
            low_price = float(low_arr[i]) if has_high_low else close_price
            exec_signal = int(signal_arr[i - 1]) if i > 0 else 0

            # 1. check risk management triggers on open position
            if active_trade is not None and active_trade.status == "OPEN":
                trigger_price, exit_reason = self.check_risk_management(active_trade, high_price, low_price)

                if trigger_price is not None and exit_reason is not None:
                    cash = self.execute_exit(cash, shares, trigger_price, current_date, active_trade, exit_reason)
                    shares = 0.0
                    active_trade = None

            # long entry signal (from previous bar)
            if exec_signal == 1 and shares == 0.0:
                cash, shares, active_trade = self.execute_long_entry(cash, close_price, ticker, current_date)

                if active_trade is not None:
                    self.trades.append(active_trade)

            # exit signal (from previous bar)
            elif exec_signal == -1 and shares > 0.0 and active_trade is not None:
                cash = self.execute_exit(cash, shares, close_price, current_date, active_trade, "SIGNAL")
                shares = 0.0
                active_trade = None

            # update daily equity tracking
            holdings_value = shares * close_price
            total_equity = cash + holdings_value

            cash_arr[i] = cash
            holdings_arr[i] = holdings_value
            equity_arr[i] = total_equity
            shares_arr[i] = shares

        # force close any remaining open position at market close on last row
        if active_trade is not None and active_trade.status == "OPEN":
            last_idx = n - 1
            close_price = float(close_arr[last_idx])
            last_date = str(timestamp_arr[last_idx]) if timestamp_arr is not None else str(last_idx)

            cash = self.execute_exit(cash, shares, close_price, last_date, active_trade, "END_OF_DATA")
            shares = 0.0

            cash_arr[last_idx] = cash
            holdings_arr[last_idx] = 0.0
            equity_arr[last_idx] = cash
            shares_arr[last_idx] = 0.0

        # write tracking columns back in one pass
        data["cash"] = cash_arr
        data["holdings"] = holdings_arr
        data["total_equity"] = equity_arr
        data["shares_held"] = shares_arr

        # calculate returns column
        data["returns"] = data["total_equity"].pct_change().fillna(0.0)
        return data

    def get_trade_log(self) -> pd.DataFrame:
        if not hasattr(self, "trades") or not self.trades:
            return pd.DataFrame()

        trade_data = []
        for t in self.trades:
            direction_str = "LONG" if t.direction == 1 else "SHORT"

            entry_price_fmt = round(t.entry_price, 4)
            exit_price_fmt = round(t.exit_price, 4) if t.exit_price is not None else None
            shares_fmt = round(t.shares, 4)
            commission_fmt = round(t.commission, 6)
            pnl_fmt = round(t.pnl, 6)
            pnl_pct_fmt = round(t.pnl_pct * 100, 4) if t.pnl_pct is not None else None

            trade_dict = {
                "ticker": t.ticker,
                "entry_date": t.entry_date,
                "exit_date": t.exit_date,
                "direction": direction_str,
                "entry_price": entry_price_fmt,
                "exit_price": exit_price_fmt,
                "shares": shares_fmt,
                "commission": commission_fmt,
                "pnl": pnl_fmt,
                "pnl_pct": pnl_pct_fmt,
                "status": t.status,
                "exit_reason": t.exit_reason,
            }
            trade_data.append(trade_dict)

        return pd.DataFrame(trade_data)
