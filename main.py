import yfinance as yf
import datetime as dt
import matplotlib

tickers = ['AAPL', 'MSFT','GOOGL','NVDA','SPY','AMZN']
data = yf.Ticker(tickers[0])
print(data.info)
print("------")
print(data.calendar)
print(data.analyst_price_targets)
print("------")

ohlcv = data.history(period="1y") # open high low close volume
print(ohlcv)

cur_time = dt.datetime.now()
start_time = cur_time - dt.timedelta(days=365*2)
complete_set = yf.download(tickers, start=start_time, end=cur_time.strftime("%Y-%m-%d"))

#save data into data.json
with open('data.json','w') as f:
    f.write(complete_set.to_json(orient='split',date_format='iso'))

print(complete_set)
for ticker in tickers:
    print(yf.Ticker(ticker).history(period="1y"))
