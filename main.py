import pandas as pd

import database
from fetcher import DataFetcher


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


if __name__ == "__main__":
    main()
