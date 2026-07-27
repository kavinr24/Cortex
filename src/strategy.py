from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from src.indicators import TechnicalIndicators

class BaseStrategy(ABC):

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # df is ohlcv dataframe with price data

    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        # calcualtes indicators and generates signals
        # must return a dataframe with a signal column
        # -1 = buy/long
        # -1 = sell/short
        # 0 = hold
        pass

class SMACrossover(BaseStrategy):

    def __init__(self, df: pd.DataFrame, fast_period: int = 50, slow_period: int = 200):
        super().__init__(df)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self) -> pd.DataFrame:
        self.df["sma_fast"] = TechnicalIndicators.sma(self.df["close"], period=self.fast_period)
        self.df["sma_slow"] = TechnicalIndicators.sma(self.df["close"], period=self.slow_period)

        self.df["signal"] = 0

        self.df["signal"] = np.where(self.df["sma_fast"] > self.df["sma_slow"], 1, 0)
        self.df["position_change"] = self.df["signal"].diff()

        return self.df


class RSIStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        super().__init__(df)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self) -> pd.DataFrame:
        # calculate rsi
        self.df["rsi"] = TechnicalIndicators.rsi(self.df["close"], period=self.period)

        signals = np.zeros(len(self.df))

        signals[self.df["rsi"] < self.oversold] = 1
        signals[self.df["rsi"] > self.overbought] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()

        return self.df

class BollingerBandsStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame, period: int = 20, num_std: float = 2.0):
        super().__init__(df)
        self.period = period
        self.num_std = num_std

    def generate_signals(self) -> pd.DataFrame:
        # calculate bollinger bands
        bb = TechnicalIndicators.bollinger_bands(self.df["close"], period=self.period, num_std=self.num_std)
        self.df["bb_upper"] = bb["bb_upper"]
        self.df["bb_middle"] = bb["bb_middle"]
        self.df["bb_lower"] = bb["bb_lower"]

        signals = np.zeros(len(self.df))

        signals[self.df["close"] < self.df["bb_lower"]] = 1
        signals[self.df["close"] > self.df["bb_upper"]] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()

        return self.df

class MACDStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(df)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def generate_signals(self) -> pd.DataFrame:
        # calculate macd
        macd = TechnicalIndicators.macd(self.df["close"], fast_period=self.fast_period, slow_period=self.slow_period, signal_period=self.signal_period)
        self.df["macd"] = macd["macd"]
        self.df["macd_signal"] = macd["macd_signal"]
        self.df["macd_hist"] = macd["macd_hist"]

        signals = np.zeros(len(self.df))

        signals[(self.df["macd"] > self.df["macd_signal"]) & (self.df["macd"].shift(1) <= self.df["macd_signal"].shift(1))] = 1
        signals[(self.df["macd"] < self.df["macd_signal"]) & (self.df["macd"].shift(1) >= self.df["macd_signal"].shift(1))] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()

        return self.df


class EMACrossover(BaseStrategy):

    def __init__(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26):
        super().__init__(df)
        self.fast_period = fast_period

    def generate_signals(self) -> pd.DataFrame:
        # exponential moving average crossover
        self.df["ema_fast"] = TechnicalIndicators.ema(self.df["close"], period=self.fast_period)
        self.df["ema_slow"] = TechnicalIndicators.ema(self.df["close"], period=self.slow_period)

        signals = np.zeros(len(self.df))

        # buy when fast crosses above slow
        signals[(self.df["ema_fast"] > self.df["ema_slow"]) & (self.df["ema_fast"].shift(1) <= self.df["ema_slow"].shift(1))] = 1
        # sell when fast crosses below slow
        signals[(self.df["ema_fast"] < self.df["ema_slow"]) & (self.df["ema_fast"].shift(1) >= self.df["ema_slow"].shift(1))] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()



class StochasticStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3, oversold: float = 20.0, overbought: float = 80.0):
        super().__init__(df)
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self) -> pd.DataFrame:
        # stochastic oscillator - %K and %D crossover with overbought/oversold
        stoch = TechnicalIndicators.stochastic(
            self.df["high"], self.df["low"], self.df["close"],
        )
        self.df["stoch_k"] = stoch["stoch_k"]
        self.df["stoch_d"] = stoch["stoch_d"]

        signals = np.zeros(len(self.df))

        # buy when K crosses above D in oversold zone
        signals[(self.df["stoh_k"] > self.df["stoch_d"]) & (self.df["stoch_k"].shift(1) <= self.df["stoch_d"].shift(1)) & (self.df["stoch_k"] < self.oversold)] = 1
        # sell when K crosses below D in overbought zone
        signals[(self.df["stoch_k"] < self.df["stoch_d"]) & (self.df["stoch_k"].shift(1) >= self.df["stoch_d"].shift(1)) & (self.df["stoch_k"] > self.overbought)] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()

        return self.df


class EMACrossover(BaseStrategy):

    def __init__(self, df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26):
        super().__init__(df)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self) -> pd.DataFrame:
        # exponential moving average crossover
        self.df["ema_fast"] = TechnicalIndicators.ema(self.df["close"], period=self.fast_period)
        self.df["ema_slow"] = TechnicalIndicators.ema(self.df["close"], period=self.slow_period)

        signals = np.zeros(len(self.df))

        # buy when fast crosses above slow
        signals[(self.df["ema_fast"] > self.df["ema_slow"]) & (self.df["ema_fast"].shift(1) <= self.df["ema_slow"].shift(1))] = 1
        # sell when fast crosses below slow
        signals[(self.df["ema_fast"] < self.df["ema_slow"]) & (self.df["ema_fast"].shift(1) >= self.df["ema_slow"].shift(1))] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()

        return self.df


class StochasticStrategy(BaseStrategy):

    def __init__(self, df: pd.DaaFrame, k_period: int = 14, d_period: int = 3, oversold: float = 20.0, overbought: float = 80.0):
        super().__nit__(df)
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self) -> pd.DataFrame:
        # stochastic oscillator - %K and %D crossover with overbought/oversold
        stoch = TechnicalIndicators.stochastic(
            self.df["high"], self.df["low"], self.df["close"],
        )
        self.df["stoch_k"] = stoch["stoch_k"]
        self.df["stoch_d"] = stoch["stoch_d"]

        signals = np.zeros(len(self.df))

        # buy when K crosses above D in oversold zone
        signals[(self.df["stoch_k"] > self.df["stoch_d"]) & (self.df["stoch_k"].shift(1) <= self.df["stoch_d"].shift(1)) & (self.df["stoch_k"] < self.oversold)] = 1
        # sell when K crosses below D in overbought zone
        signals[(self.df["stoch_k"] < self.df["stoch_d"]) & (self.df["stoch_k"].shift(1) >= self.df["stoch_d"].shift(1)) & (self.df["stoch_k"] > self.overbought)] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()



class ADXStrategy(BaseStrategy):

    def __init__(self, df: pd.DataFrame, period: int = 14, adx_threshold: float = 25.0):
        super().__init__(df)
        self.period = period
        self.adx_threshold = adx_threshold

    def _plus_di(self) -> pd.Series:
        # +DI calculation
        prev_high = self.df["high"].shift(1)
        prev_low = self.df["low"].shift(1)
        plus_dm = (self.df["high"] - prev_high).clip(lower=0)
        minus_dm = (prev_low - self.df["low"]).clip(lower=0)
        plus_dm[plus_dm < minus_dm] = 0
        minus_dm[minus_dm < plus_dm] = 0

        prev_close = self.df["close"].shift(1)
        tr1 = self.df["high"] - self.df["low"]
        tr2 = (self.df["high"] - prev_close).abs()
        tr3 = (self.df["low"] - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = true_range.ewm(alpha=1/self.period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=self.period, adjust=False).mean() / atr)
        return plus_di

    def _minus_di(self) -> pd.Series:
        # -DI calculation
        prev_high = self.df["high"].shift(1)
        prev_low = self.df["low"].shift(1)
        plus_dm = (self.df["high"] - prev_high).clip(lower=0)
        minus_dm = (prev_low - self.df["low"]).clip(lower=0)
        plus_dm[plus_dm < minus_dm] = 0
        minus_dm[minus_dm < plus_dm] = 0

        prev_close = self.df["close"].shift(1)
        tr1 = self.df["high"] - self.df["low"]
        tr2 = (self.df["high"] - prev_close).abs()
        tr3 = (self.df["low"] - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = true_range.ewm(alpha=1/self.period, adjust=False).mean()
        minus_di = 100 * (minus_dm.ewm(alpha=1/self.period, adjust=False).mean() / atr)
        return minus_di

    def generate_signals(self) -> pd.DataFrame:
        # adx with +di and -di crossover for trend direction
        self.df["adx"] = TechnicalIndicators.adx(self.df["high"], self.df["low"], self.df["close"], period=self.period)
        self.df["plus_di"] = self._plus_di()
        self.df["minus_di"] = self._minus_di()

        signals = np.zeros(len(self.df))

        # only trade when trend is strong enough

        # buy when +DI crosses above -DI in a strong trend
        signals[(self.df["plus_di"] > self.df["minus_di"]) & (self.df["plus_di"].shift(1) <= self.df["minus_di"].shift(1)) & strong_trend] = 1
        # sell when -DI crosses above +DI in a strong trend
        signals[(self.df["minus_di"] > self.df["plus_di"]) & (self.df["minus_di"].shift(1) <= self.df["plus_di"].shift(1)) & strong_trend] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()



class ATRStrategy(BaseStrategy):

    def __init__(self, df: pd.Dataame, atr_period: int = 14, atr_multiplier: float = 1.5):
        super().__init__(df)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

    def generate_signals(self) -> pd.DataFrame:
        # atr channel breakout - price breaks above/below ATR envelope around sma
        self.df["atr"] = TechnicalIndicators.atr(self.df["high"],self.df["low"], self.df["close"], period=self.atr_period)
        self.df["sma_20"] = TechnicalIndicators.sma(self.df["close"], period=20)

        # upper and lower channels
        upper_channel = self.df["sma_20"] + (self.df["atr"] * self.atr_multiplier)
        lower_channel = self.df["sma_20"] - (self.df["atr"] * self.atr_multiplier)

        self.df["atr_upper"] = upper_channel
        self.df["atr_lower"] = lower_channel

        signals = np.zeros(len(self.df))

        # buy when price breaks above upper channel
        signals[(self.df["close"] > upper_channel) & (self.df["close"].shift(1) <= upper_channel.shift(1))] = 1
        # sell when price breaks below lower channel
        signals[(self.df["close"] < lower_channel) & (self.df["close"].shift(1) >= lower_channel.shift(1))] = -1

        self.df["signal"] = signals
        self.df["position_change"] = self.df["signal"].diff()

