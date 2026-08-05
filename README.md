# Cortex Backtesting Engine

A backtesting engine and live charting dashboard.

Cortex is a small app for fetching price data, building simple rule based strategies (or selecting from prebuilt strategies), and running quick backtests on any stock ticker you want inside an easy-to-navigate dashboard.

## Features

- Flexible data sources: load OHLCV from CSV or JSON, or fetch market data (e.g., Yahoo Finance).
- Built-in technical indicators: SMA, EMA, RSI, Bollinger Bands, MACD, Stochastic Oscillator, ADX, ATR.
- Visual Strategy Builder: create rule-based entry/exit logic with a live preview and quick backtest.
- Fast, lightweight backtester with a simple execution model, commission/slippage support, an easy to understand trade log, and an equity curve.
- Interactive Streamlit UI for tweaking rules, parameters, and backtest settings in the browser.
- Exportable results: download generated signals or tables for offline analysis and sharing in CSV and JSON.

## Tech Stack

- Python 3.14
- pandas, numpy, yfinance
- Streamlit (UI)
- Render (Deployment)
- SQLite (Database)

## Want to run Cortex locally?

1. Create a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the Streamlit app:

```bash
streamlit run app.py
```

The app will open in your browser, or just use `localhost:8501`.

## Strategy Builder Usage

1. In the sidebar enable `Open Strategy Builder`.
2. The preview table includes a few precomputed indicators (`sma_10`, `sma_30`, `ema_9`).
3. Add entry and exit rules. Example rule pairs that produce trades:

- Candle flip (frequent trades):
  - Entry: `close` > `open` (Column)
  - Exit: `close` < `open` (Column)

- SMA crossover:
  - Entry: `sma_10` crosses_above `sma_30`
  - Exit: `sma_10` crosses_below `sma_30`

4. Click `Apply Strategy`, expand Backtest Settings if you want to change capital/fees, then review `Backtest Results` and the `Trade Log`.

## Development

- The core strategy logic lives in `src/builder.py` and `src/strategy.py`.
- Backtest simulation is in `src/backtester.py`.
- UI code is in the `app/` folder.

- ### Tools used for development + Credits
    - Visual Studio Code (most of the project was done in this IDE)
    - Copilot line completion - helped will all coding
    - Gemini - helped with planning and taught me alot about quantitative trading & backtesting, & helped with errors/problems
    - Copilot - used for debugging and formatting
    - Opencode - used for debugging and formatting
        - Copilot (and Opencode when I ran out of Copilot credits) were used throughout the project for some implementation & debugging, especially alot more towards the end during deployment. I encountered a large amount of different errors when trying to deploy to Render, and they helped with fixing these bugs to prepare for deployment. Gemini helped with research on these errors.
        - They were also used for last bug checks and usability checks, after I had done my full manual runthrough.
    

