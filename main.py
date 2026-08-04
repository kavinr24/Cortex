import os
import pandas as pd
import src.database as database
from src.fetcher import DataFetcher
from src.indicators import TechnicalIndicators
from src.strategy import SMACrossover, RSIStrategy
from src.backtester import Backtester
from src.metrics import PerformanceMetrics
from src.builder import CustomStrategy

def main():
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "SPY", "AMZN"]
    db = "cortex_market_data.db"
    json_file = "formatted_data.json"
    csv_file = "formatted_data.csv"

    fetcher = DataFetcher(tickers=tickers, years=2)
    flat_table_data = fetcher.fetch_ohlcv()

    with open(json_file, "w") as f:
        f.write(flat_table_data.to_json(orient="records", date_format="iso"))
        print("exported to", json_file)

    with open(csv_file, "w") as f:
        f.write(flat_table_data.to_csv(index=False))
        print("exported records to", csv_file)

    verify_df = pd.read_json(json_file)
    print("Records per ticker:")
    print(verify_df.groupby("ticker").size())

    manager = database.DatabaseManager(db_path=db)
    manager.save_ohlcv(flat_table_data)
    print("inserted records into db")

    summary_df = manager.get_summary()
    print("DB records summary")
    print(summary_df.to_string(index=False))
    print("AAPL SAMPLE QUERY")
    sample_df = manager.load_ticker_data("AAPL").head(5)
    print(sample_df.to_string(index=False))

    print("indicator testing")

    sample_df = manager.load_ticker_data("AAPL")

    sample_df["sma_20"] = TechnicalIndicators.sma(sample_df["close"], period=20)
    sample_df["ema_20"] = TechnicalIndicators.ema(sample_df["close"], period=20)
    sample_df["rsi_14"] = TechnicalIndicators.rsi(sample_df["close"], period=14)

    cols_to_print = ["timestamp","close", "sma_20", "ema_20", "rsi_14"]

    print("EARLY SAMPLE")
    print(sample_df[cols_to_print].head(20).to_string(index=False))

    print("RECENT SAMPLE")
    print(sample_df[cols_to_print].tail(10).to_string(index=False))

    #strategy testing

    aapl_df = manager.load_ticker_data("AAPL")

    print("STRATEGY TESTING")
    print("SMA CROSSOVER 20/50")
    sma_strat = SMACrossover(aapl_df, fast_period=20, slow_period=50)
    sma_results = sma_strat.generate_signals()
    sma_cols = ["timestamp","close","sma_fast","sma_slow","signal","position_change"]
    print(sma_results[sma_cols].tail(10).to_string(index=False))

    print("RSI STRATEGY 14, 30/70")
    rsi_strat = RSIStrategy(aapl_df, period=14, oversold=30.0, overbought=70.0)
    rsi_results = rsi_strat.generate_signals()
    rsi_cols = ["timestamp","close","rsi","signal","position_change"]
    print(rsi_results[rsi_cols].tail(10).to_string(index=False))

    print("BUILDER TESTING")
    # create simple moving averages and test CustomStrategy builder
    builder_df = aapl_df.copy()
    builder_df["sma_10"] = TechnicalIndicators.sma(builder_df["close"], period=10)
    builder_df["sma_30"] = TechnicalIndicators.sma(builder_df["close"], period=30)

    custom = CustomStrategy(builder_df)
    # entry when sma_10 crosses above sma_30, exit when it crosses below
    custom.add_entry("sma_10", "cross_above", "sma_30")
    custom.add_exit("sma_10", "cross_below", "sma_30")
    custom_results = custom.generate_signals()
    print(custom_results[["timestamp","close","sma_10","sma_30","signal","position_change"]].tail(10).to_string(index=False))

    print("BACKTESTING")
    # run a simple backtest using the SMA crossover signals
    try:
        bt = Backtester(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage_rate=0.0005,
            position_size_pct=0.95,
            stop_loss_pct=0.05,
            take_profit_pct=0.1,
        )

        # use sma_results if available and it contains 'signal'
        if 'sma_results' in locals() and 'signal' in sma_results.columns:
            backtest_df = bt.run(sma_results)
            print('backtest final equity:', backtest_df['total_equity'].iloc[-1])
            print('Trade log:')
            print(bt.get_trade_log().to_string(index=False))

            print("PERFORMANCE METRICS")

            metrics = PerformanceMetrics(
                backtest_df = backtest_df,
                trade_log = bt.get_trade_log(),
                initial_capital = 100000.0
                                         )
            metrics.summary()


        else:
            print('NO SMA signals available for backtesting')
    except Exception as e:
        print('backtest failed D: (', e, ')')


    

    


if __name__ == "__main__":
    main()
