import sqlite3

with sqlite3.connect("asdf.db") as conn:
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
