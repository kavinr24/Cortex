import yfinance as yf
import datetime as dt
import matplotlib as mpl
import pandas as pd
import sqlite3


tickers = ['AAPL', 'MSFT','GOOGL','NVDA','SPY','AMZN']
db = "cortex_market_data.db"
json_file = "formatted_data.json"
csv_file = "formatted_data.csv"

cur_time = dt.datetime.now()
start_time = cur_time - dt.timedelta(days=365*2)
raw = yf.download(tickers, 
                           start=start_time.strftime("%Y-%m-%d"), 
                           end=cur_time.strftime("%Y-%m-%d"),
                           group_by='ticker')


# raw is a multi index dataframe
# reformat raw into flat table

print("RAW REFORMAT")

df_aapl = raw["AAPL"].dropna().copy()
print(df_aapl) 
df_aapl.reset_index(inplace=True)

records = []
for ticker in tickers:
    if ticker in raw.columns:
        df_ticker = raw[ticker].dropna().copy()
        df_ticker.reset_index(inplace=True)
        df_ticker['ticker'] = ticker
        columns = ['ticker','timestamp','open','high','low','close','volume']
        mapping = {
            'Date': 'timestamp',
            'Datetime': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        df_ticker.rename(columns=mapping, inplace=True)
        #format
        df_ticker["timestamp"] = df_ticker["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        records.append(df_ticker[columns])

flat_table_data = pd.concat(records, ignore_index=True)
complete_set = flat_table_data.copy()

# export to json
with open(json_file, 'w') as f:
    f.write(flat_table_data.to_json(orient='records', date_format='iso'))
    print("exported to ",json_file)

# export to csv
with open(csv_file, 'w') as f:
    f.write(flat_table_data.to_csv(index=False))
    print("exported records to ",csv_file)

# verify json data
verify_df = pd.read_json(json_file)
print("Records per ticker:")
print(verify_df.groupby('ticker').size())

print("creating sqlite database")
with sqlite3.connect(db) as conn:
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

    flat_table_data.to_sql("ohlcv",conn,if_exists="replace",index=False)
    print("inserted records into db")


    # verification
    with sqlite3.connect(db) as conn:
        summary_query = pd.read_sql_query("SELECT ticker, COUNT(*) as row_count, MIN(timestamp) as start_date, MAX(timestamp) as end_date FROM ohlcv GROUP BY ticker",
                                          conn,
                                          )
        print("DB records summmary")
        print(summary_query.to_string(index=False))

    #test query by fetching AAPL data
    print("AAPL SAMPLE QUERY")
    sample = "SELECT * FROM ohlcv WHERE ticker = ? ORDER BY timestamp ASC LIMIT 5" 
    sample_df = pd.read_sql_query(sample, conn, params=("AAPL",))
    print(sample_df.to_string(index=False))




# conn = sqlite3.connect('cortex_market_data.db')
