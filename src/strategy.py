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
