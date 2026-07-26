from dataclasses import dataclass
from typing import List, Optional, Tuple
import pandas as pd


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
        self.initial_capital = float(initial_capital)
        self.commission_rate = float(commission_rate)
        self.slippage_rate = float(slippage_rate)
        self.position_size_pct = float(position_size_pct)
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trades: List[Trade] = []

    def calculate_adjusted_entry_price(self, close_price: float) -> float:
        return close_price * (1 + self.slippage_rate)

    def calculate_adjusted_exit_price(self, exit_price: float) -> float:
        return exit_price * (1 - self.slippage_rate)

    def calculate_commission(self, total_value: float) -> float:
        return total_value * self.commission_rate

    def calculate_position_size(self, cash: float, entry_price: float) -> float:
        if entry_price <= 0:
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

        if cash < total_cost:
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


        if trade.entry_price > 0:
            trade.pnl = (exit_price_adj - trade.entry_price) * trade.shares - trade.commission
            trade.pnl_pct = trade.pnl / (trade.entry_price * trade.shares)
            
        trade.status = "CLOSED"
        trade.exit_reason = reason

        return new_cash

    def run(self, df: pd.DataFrame, ticker: str = "ASSET") -> pd.DataFrame:
        data = df.copy().reset_index(drop=True)

        # verify required columns exist
        if "close" not in data.columns:
            raise ValueError("DataFrame must contain 'close' column")

        has_high_low = "high" in data.columns and "low" in data.columns

        # setup output tracking columns
        data["cash"] = 0.0
        data["holdings"] = 0.0
        data["total_equity"] = 0.0
        data["shares_held"] = 0.0

        cash = float(self.initial_capital)
        shares = 0.0
        self.trades = []
        active_trade: Optional[Trade] = None

        
        # main simulation loop
        for i in range(len(data)):
            current_date = str(data.loc[i, "timestamp"]) if "timestamp" in data.columns else str(i)
            close_price = float(data.loc[i, "close"])
            high_price = float(data.loc[i, "high"]) if has_high_low else close_price
            low_price = float(data.loc[i, "low"]) if has_high_low else close_price
            signal = int(data.loc[i, "signal"]) if "signal" in data.columns else 0

            # 1. check risk management triggers on open position
            if active_trade is not None and active_trade.status == "OPEN":
                trigger_price, exit_reason = self.check_risk_management(active_trade, high_price, low_price)

                if trigger_price is not None and exit_reason is not None:
                    cash = self.execute_exit(cash, shares, trigger_price, current_date, active_trade, exit_reason)
                    shares = 0.0
                    active_trade = None

            # long entry signal
            if signal == 1 and shares == 0.0:
                cash, shares, active_trade = self.execute_long_entry(cash, close_price, ticker, current_date)

                if active_trade is not None:
                    self.trades.append(active_trade)

            # exit signal
            elif signal == -1 and shares > 0.0 and active_trade is not None:
                cash = self.execute_exit(cash, shares, close_price, current_date, active_trade, "SIGNAL")
                shares = 0.0
                active_trade = None

            # update daily equity tracking
            holdings_value = shares * close_price
            total_equity = cash + holdings_value

            data.loc[i, "cash"] = cash
            data.loc[i, "holdings"] = holdings_value
            data.loc[i, "total_equity"] = total_equity
            data.loc[i, "shares_held"] = shares

        # force close any remaining open position at market close on last row
        if active_trade is not None and active_trade.status == "OPEN":
            last_idx = len(data) - 1
            close_price = float(data.loc[last_idx, "close"])
            last_date = str(data.loc[last_idx, "timestamp"]) if "timestamp" in data.columns else str(last_idx)

            cash = self.execute_exit(cash, shares, close_price, last_date, active_trade, "END_OF_DATA")
            shares = 0.0

            data.loc[last_idx, "cash"] = cash
            data.loc[last_idx, "holdings"] = 0.0
            data.loc[last_idx, "total_equity"] = cash
            data.loc[last_idx, "shares_held"] = 0.0

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
            exit_price_fmt = round(t.exit_price, 4) if t.exit_price else None
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
