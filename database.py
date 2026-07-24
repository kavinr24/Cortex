import sqlite3
import pandas as pd

class DatabaseManager:

    def __init__(self, db_path: str="data/cortex_market_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # creates the ohlcv table if it doesn't exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ohlcv (
                    ticker TEXT,
                    timestamp TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker, timestamp)
                )
                
            """
            )
        conn.commit()

    def save_ohlcv(self, df: pd.DataFrame):
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql('ohlcv', conn, if_exists='append', index=False)

    def load_ticker_data(self, ticker:str) -> pd.DataFrame:
        # load data for a ticker from the db
        query = (
            "SELECT * FROM ohlcv WHERE ticker = ? ORDER BY timestamp ASC"
        )
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=(ticker,))

    def get_summary(self):
        # returns row coutns and data bounds for each ticker
        query = """
            SELECT
                ticker,
                COUNT(*) as row_count,
                MIN(timestamp) as start_date,
                MAX(timestamp) as end_date
            FROM ohlcv
            GROUP BY ticker
    
        """
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

