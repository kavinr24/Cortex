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

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        # bollinger bands - upper, middle, lower
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        return pd.DataFrame({"bb_upper": upper, "bb_middle": middle, "bb_lower": lower})

    @staticmethod
    def macd(series: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        # moving average convergence divergence
        fast_ema = series.ewm(span=fast_period, adjust=False).mean()
        slow_ema = series.ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        return pd.DataFrame({"macd": macd_line, "macd_signal": signal_line, "macd_hist": histogram})

    @staticmethod
    def stochastic(high: pd.Series, low:pd.Series, close: pd.Seires, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        # stochastic oscillator - %K and %D
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = ((close-lowest_low)/(highest_high-lowest_low))*100
        d = k.rolling(window=d_period).mean()
        return pd.DataFrame({"stoch_k":k, "stoch_d":d})

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        # avg directional index - trend strength
        prev_high = high.shift(1)
        prev_low = low.shift(1)

        # zero out when other dm is larger
        plus_dm = (high-prev_high).clip(lower=0)
        minus_dm = (prev_low-low).clip(lower=0)

        plus_dm[plus_dm<minus_dm] = 0
        minus_dm[minus_dm<plus_dm] = 0

        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high-prev_close).abs()
        tr3 = (low-prev_close).abs()

        true_range = pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)

        atr = true_range.ewm(alpha=1/period,adjust=False).mean()
        plus_di = 100*(plus_dm.ewm(alpha=1/period,adjust=False).mean()/atr)
        minus_di = 100*(minus_dm.ewm(alpha=1/period,adjust=False).mean()/atr)


        dx = (abs(plus_di-minus_di)/(plus_di+minus_di))*100
        adx = dx.ewm(alpha=1/period,adjust=False).mean()
        return adx


    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
         # average true range (volatility)
         prev_close = close.shift(1)
         tr1 = high-low
         tr2 = (high-prev_close).abs()
         tr3 = (low-prev_close).abs()
         true_range = pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)

