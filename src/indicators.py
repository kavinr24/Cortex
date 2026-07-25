import pandas as pd

class TechnicalIndicators:
    # TA indicators calculated on pandas Series

    @staticmethod
    def sma(series: pd.Series, period: int = 20) -> pd.Series:
        # simple moving average
        return series.rolling(window=period).mean()

    @staticmethod
    # exponential moving average
    def ema(series: pd.Series, period: int = 20) -> pd.Series:
        return series.ewm(span=period,adjust=False).mean()

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        # relative strength index
        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -1*delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/period,min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period,min_periods=period, adjust=False).mean()

        rs = avg_gain/avg_loss
        rsi = 100 - (100/(1+rs))
        return rsi
