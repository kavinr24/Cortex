import yfinance as yf
import datetime as dt
import matplotlib as mpl
import pandas as pd


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



# conn = sqlite3.connect('cortex_market_data.db')
