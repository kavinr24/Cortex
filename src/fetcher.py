import datetime as dt
import pandas as pd
import yfinance as yf

class DataFetcher:

    def __init__(self, tickers: list[str], years: int = 2):
        self.tickers = tickers
        self.years = years

    def fetch_ohlcv(self) -> pd.DataFrame:
        # downloads raw data and returns a dataframe with columns:
        # ticker, timestamp, open, high, low, close, volume
        cur_time = dt.datetime.now()
        start_time = cur_time - dt.timedelta(days=365 * self.years)

        raw_data = yf.download(
            self.tickers,
            start=start_time.strftime("%Y-%m-%d"),
            end=cur_time.strftime("%Y-%m-%d"),
            group_by='ticker'
        )
        records = []
        for ticker in self.tickers:
            # yfinance returns a MultiIndex for multiple tickers but a plain Index for one
            if isinstance(raw_data.columns, pd.MultiIndex):
                if ticker not in raw_data.columns.levels[0]:
                    continue
                df_ticker = raw_data[ticker].dropna().copy()
            else:
                if raw_data.empty or ticker != self.tickers[0]:
                    continue
                df_ticker = raw_data.dropna().copy()
            df_ticker.reset_index(inplace=True)
            df_ticker["ticker"] = ticker

            column_mapping = {
                "Date": "timestamp",
                "Datetime": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }
            df_ticker.rename(columns=column_mapping, inplace=True)
            df_ticker["timestamp"] = df_ticker["timestamp"].astype(str)

            cols = [
                "ticker",
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
            records.append(df_ticker[cols])

        return pd.concat(records, ignore_index=True)
    



