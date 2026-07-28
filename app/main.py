import tkinter as tk
from time import sleep

tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "SPY", "AMZN"]
root = tk.Tk(screenName="Cortex")
root.title("Cortex")
root.geometry("1000x500")
label = tk.Label(root, text="Ticker:")
label.place(x=10, y=10)

labels = {}

entry = tk.Entry(root, width=25)
entry.place(x=10, y=40)


def test():
    print("submitted", entry.get())
    if entry.get().upper() not in tickers:
        button.configure(text="invalid ticker. try again.")
    else:
        button.configure(text="valid ticker. loading...")
        sleep(1)
        load_ui()


def load_ui():
    button.configure(text="check")
    labels["logs_title"] = tk.Label(root, text="Logs")
    labels["logs_title"].place(x=200,y=10)
    labels["logs"] = tk.Label(root, text="start backtesting, and trades will appear here.")
    labels["logs"].place(x=200,y=30)

button = tk.Button(root,text="check",command=test)
button.place(x=10,y=70)


root.mainloop()