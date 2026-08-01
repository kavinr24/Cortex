from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd


# data transfer object
@dataclass
class BacktestPayload:
    metrics: dict = field(default_factory=dict)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades: pd.DataFrame = field(default_factory=pd.DataFrame)
    logs: list = field(default_factory=list)


# bridge controller
class CortexBridge:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(__file__).resolve().parent.parent / data_dir

    def execute_backtest(self, ui_params: dict) -> BacktestPayload:
        logs = []
        logs.append(f"[BRIDGE] Initializing pipeline for ticker: {ui_params.get('symbol', 'NVDA')}")

        try:
            # load price data
            df, data_log = self._load_data(
                symbol=ui_params.get("symbol", "NVDA"),
                timeframe=ui_params.get("timeframe", "1D")
            )
            logs.append(data_log)

            # generate signals
            df, strat_log = self._compute_strategy(df, ui_params)
            logs.append(strat_log)

            # simulate execution in portfolio
            df, trades_df, metrics, sim_log = self._simulate_portfolio(df, ui_params)
            logs.append(sim_log)

            logs.append("[BRIDGE] Backtest completed successfully.")

            return BacktestPayload(
                metrics=metrics,
                equity_curve=df,
                trades=trades_df,
                logs=logs
            )

        except Exception as e:
            logs.append(f"[ERROR] Engine failure: {str(e)}")
            return self._build_fallback_payload(ui_params, logs)

    # pipeline methods
    def _load_data(self, symbol: str, timeframe: str) -> tuple[pd.DataFrame, str]:
        # checks db, csv, or generates data if nothing exists
        db_path = self.data_dir / "market_data.db"
        csv_path = self.data_dir / f"{symbol.lower()}_{timeframe.lower()}.csv"

        if db_path.exists():
            conn = sqlite3.connect(db_path)
            query = "SELECT timestamp, open, high, low, close, volume FROM price_data WHERE symbol = ? ORDER BY timestamp ASC"
            df = pd.read_sql_query(query, conn, params=(symbol,), parse_dates=["timestamp"])
            conn.close()
            log_msg = f"[DATA] Loaded {len(df)} records from db."
        elif csv_path.exists():
            df = pd.read_csv(csv_path, parse_dates=["timestamp"])
            log_msg = f"[DATA] Loaded {len(df)} records from CSV ({csv_path.name})."
        else:
            df = self._generate_synthetic_ohlcv(symbol)
            log_msg = f"[DATA] Local data file not found. Generated dataset ({len(df)} bars)."

        df.columns = [c.capitalize() for c in df.columns]
        if "Timestamp" in df.columns:
            df.set_index("Timestamp", inplace=True)

        return df, log_msg

    def _compute_strategy(self, df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
        # calculates indicators and signals based on strategy parameters
        data = df.copy()

        fast_period = int(params.get("fast_ema", 20))
        slow_period = int(params.get("slow_ema", 50))

        # technical indicators
        data["Fast_EMA"] = data["Close"].ewm(span=fast_period, adjust=False).mean()
        data["Slow_EMA"] = data["Close"].ewm(span=slow_period, adjust=False).mean()

        # 1=long, -1=short, 0=flat
        data["Signal"] = np.where(data["Fast_EMA"] > data["Slow_EMA"], 1, -1)

        # apply rsi filter if enabled
        if params.get("use_rsi", False):
            delta = data["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            data["RSI"] = 100 - (100 / (1 + rs))

            # stop longs if RSI > 70 (overboughtr)
            data["Signal"] = np.where((data["Signal"] == 1) & (data["RSI"] > 70), 0, data["Signal"])

        # shift signals so that trades are executed on the next bar after signal generation
        data["Position"] = data["Signal"].shift(1).fillna(0)

        log = f"[STRATEGY] Computed signals ({params.get('strategy', 'Custom')}) -  Fast EMA: {fast_period}, Slow EMA: {slow_period}"
        return data, log

    def _simulate_portfolio(self, df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict, str]:
        # simulates portfolio performance based on signals abd capital
        data = df.copy()

        capital = float(params.get("capital", 100000.0))
        comm_pct = float(params.get("commission", 0.10)) / 100.0
        slip_pct = float(params.get("slippage", 0.05)) / 100.0
        total_friction = comm_pct + slip_pct

        # asset returns
        data["Market_Returns"] = data["Close"].pct_change().fillna(0)
        data["Strategy_Returns"] = data["Position"] * data["Market_Returns"]

        # apply friction costs on entry/exit
        position_changes = data["Position"].diff().fillna(0) != 0
        data["Strategy_Returns"] = np.where(position_changes,
                                            data["Strategy_Returns"] - total_friction,
                                            data["Strategy_Returns"])

        # calculate equity curve
        data["Portfolio_Value"] = capital * (1 + data["Strategy_Returns"]).cumprod()

        # PA
        final_balance = data["Portfolio_Value"].iloc[-1]
        net_pnl = final_balance - capital
        total_return_pct = (net_pnl / capital) * 100

        rolling_max = data["Portfolio_Value"].cummax()
        drawdown = (data["Portfolio_Value"] - rolling_max) / rolling_max
        max_drawdown_pct = drawdown.min() * 100

        sharpe = self._calculate_sharpe_ratio(data["Strategy_Returns"])

        # create df for executed trades
        trades_df = self._build_trade_log(data)
        win_rate = self._calculate_win_rate(trades_df)

        metrics = {
            "total_return": f"{total_return_pct:+.2f}%",
            "final_balance": f"${final_balance:,.2f}",
            "net_pnl": f"${net_pnl:,.2f}",
            "max_drawdown": f"{max_drawdown_pct:.2f}%",
            "sharpe_ratio": f"{sharpe:.2f}",
            "win_rate": f"{win_rate:.1f}%",
            "total_trades": len(trades_df)
        }

        log = f"[SIMULATOR] Capital: ${capital:,.2f} ----> Final: ${final_balance:,.2f} - Return: {total_return_pct:+.2f}%"
        return data, trades_df, metrics, log


    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        std = returns.std()
        if std == 0 or np.isnan(std):
            return 0.0
        return float((returns.mean() - risk_free_rate) / std * np.sqrt(252))

    def _calculate_win_rate(self, trades_df: pd.DataFrame) -> float:
        if trades_df.empty or "Net PnL ($)" not in trades_df.columns:
            return 0.0
        winning_trades = (trades_df["Net PnL ($)"] > 0).sum()
        return float((winning_trades / len(trades_df)) * 100)

    def _build_trade_log(self, df: pd.DataFrame) -> pd.DataFrame:
        # finds rows were position changes occur and logs the trade details
        events = df[df["Position"].diff().fillna(0) != 0].copy()
        if events.empty:
            return pd.DataFrame()

        records = []
        for i in range(len(events)):
            row = events.iloc[i]
            pos_type = "LONG" if row["Position"] > 0 else ("SHORT" if row["Position"] < 0 else "FLAT")

            pnl = row["Portfolio_Value"] - (events.iloc[i - 1]["Portfolio_Value"] if i > 0 else row["Portfolio_Value"])

            records.append({
                "Trade ID": f"TRD-{101 + i}",
                "Date": events.index[i].strftime("%Y-%m-%d"),
                "Position": pos_type,
                "Price ($)": round(row["Close"], 2),
                "Portfolio Value ($)": round(row["Portfolio_Value"], 2),
                "Net PnL ($)": round(pnl, 2)
            })

        return pd.DataFrame(records)

    def _generate_synthetic_ohlcv(self, symbol: str) -> pd.DataFrame:
        # synthetic fallback data generator
        dates = pd.date_range(end=pd.Timestamp.now(), periods=180, freq="D")
        np.random.seed(hash(symbol) % 2 ** 32)
        returns = np.random.normal(loc=0.0008, scale=0.018, size=180)
        price = 150.0 * np.cumprod(1 + returns)

        df = pd.DataFrame({
            "Open": price * (1 - 0.002),
            "High": price * (1 + 0.008),
            "Low": price * (1 - 0.008),
            "Close": price,
            "Volume": np.random.randint(50000, 200000, size=180)
        }, index=dates)
        df.index.name = "Timestamp"
        return df

    def _build_fallback_payload(self, params: dict, logs: list) -> BacktestPayload:
        # returns safe default objects in case theres exceptiond during backtest execution
        df = self._generate_synthetic_ohlcv("NVDA")
        df["Portfolio_Valur"] = params.get("capital",100000.0)
        metrics = {
            "total_return": "0.00%",
            "final_balance": f"${params.get('capital', 100000.0):,.2f}",
            "net_pnl": "$0.00",
            "max_drawdown": "0.00%",
            "sharpe_ratio": "0.00",
            "win_rate": "0.0%",
            "total_trades": 0
        }

        return BacktestPayload(metrics=metrics, equity_curve=df, trades=pd.DataFrame(),logs=logs)