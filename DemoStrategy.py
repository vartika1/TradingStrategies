#@goal:To trade assets using Bollinger Band
from urllib.parse import urlparse, urlencode
import urllib
import json
import pandas as pd
import numpy as np
import datetime as dt
class BaseStrategy:
    def __init__(self):
        pass

    def generate_signals(self):
        pass

    def calculate_positions(self):
        pass


import numpy as np

#/***************************BOLLINGER BAND STRATEGY********************************************/#
class BollingerBandStrategy(BaseStrategy):
    def __init__(self, ma_window=20, stddev_multiplier=2, rsi_window=14):
        super().__init__()
        self.ma_window = ma_window
        self.stddev_multiplier = stddev_multiplier
        self.rsi_window = rsi_window

    def generate_signals(self, data):
        print("entered here")

        # Calculate moving average and standard deviation with a rolling window
        data['ma'] = data['close'].rolling(self.ma_window).mean()
        data['stddev'] = data['close'].rolling(self.ma_window).std()
        #data.dropna(inplace=True)  # Remove NaN values
        # Calculate Bollinger Bands
        data['lowerBand'] = data['ma'] - (self.stddev_multiplier * data['stddev'])
        data['upperBand'] = data['ma'] + (self.stddev_multiplier * data['stddev'])
        #data.dropna(inplace=True) # Remove NaN values
        # Calculate RSI
        delta = data['close'].diff(1)
        data['gain'] = delta.where(delta > 0, 0).rolling(self.rsi_window).mean()
        data['loss'] = -delta.where(delta < 0, 0).rolling(self.rsi_window).mean()
        data.loc[(data['loss'] != 0), 'MAR'] = data['gain']/ data['loss']
        data['RSI'] = 100 - (100 / (1 + data['MAR']))
        #data.dropna(inplace=True)  # Remove NaN values

        # Generate signals based on Bollinger Bands and RSI
        data['signal'] = 0
        data.loc[((data['close'] > data['upperBand']) & (data['RSI'] > 70)), 'signal'] = -1
        data.loc[((data['close'] < data['lowerBand']) & (data['RSI'] < 30)), 'signal'] = 1
        #data.dropna(inplace=True)  # Remove NaN values
        #print(data)

        return data

    def generate_position(self, data):
        # Fill forward positions based on signals
        data['position'] = data['signal'].replace(to_replace=0, method='ffill')



#/***************************MOVING AVERAGE STRATEGY********************************************/#
class MovingAverageStrategy(BaseStrategy):
    def __init__(self, data, sma=20, lma = 100):
        super().__init__()
        self.sma = sma
        self.lma = lma

    def generate_signals(self):
        data['SMA'] = data['price'].rolling(window=sma).mean()
        data['LMA'] = data['price'].rolling(window=lma).mean()
        data['SMA_prev'] = data['SMA'].shift(1)
        data['LMA_prev'] = data['LMA'].shift(1)
        data.loc[:, 'signal'] = np.where((data['SMA_prev'] < data['LMA_prev']) & (data['SMA'] > data['LMA']), 1, 0)
        data.loc[:, 'signal'] = np.where((data['SMA_prev'] > data['LMA_prev']) & (data['SMA'] < data['LMA']), -1, data['signal'])


    def generate_position(self, data):
        # Fill forward positions based on signals
        data['position'] = data['signal'].replace(to_replace=0, method='ffill')



