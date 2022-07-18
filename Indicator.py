import numpy as np
import talib

from settings import SYMBOL


class Indicator:
    def __init__(self):
        self.slow_speed_line = 0
        self.fast_primary_trend_line = 0
        self.trend_line_1 = 0
        self.trend_line_2 = 0
        self.trend_line_3 = 0
        self.no_trend_zone_middle_line = 0
        self.long_signal_candle = False
        self.short_signal_candle = False
#        self.no_trend_zone_upper_line = trade_bot_obj.upper_and_lower_trend_zone_line(high, low, close) + 2.6

    def trigger_candle_45_per(self, open, high, low, close, shadow_range):
        a = abs(high - low)
        b = abs(close - open)
        c = shadow_range / 100
        rv = b < c * a
        x = low + (c * a)
        y = high - (c * a)

        long_bar = rv == 1 and high > y and close < y and open < y
        short_bar = rv == 1 and low < x and close > x and open > x

        return long_bar, short_bar

    def calculate(self, open_price, high, low, close):
        close = np.array(close)
        self.slow_speed_line = talib.SMA(close, 5)[-1]
        self.fast_primary_trend_line = talib.EMA(close, 18)[-1]
        self.trend_line_1 = talib.SMA(close, 50)[-1]
        self.trend_line_2 = talib.SMA(close, 89)[-1]
        self.trend_line_3 = talib.EMA(close, 144)[-1]
        self.no_trend_zone_middle_line = talib.EMA(close, 35)[-1]
        self.long_signal_candle, self.short_signal_candle = self.trigger_candle_45_per(np.array(open_price)[-2],
                                                                                      np.array(high)[-2],
                                                                                      np.array(low)[-2],
                                                                                      np.array(close)[-2], 45)

    def first_print(self, currency_price):
        print("\n--------- Currency ---------")
        print(SYMBOL, ":", currency_price)
        print("----------------------------")
        print("\n************** Strategy Result First Run ***********")
        print("Slow Speed Line: ", self.slow_speed_line)
        print("Fast Primary Trend Line: ", self.fast_primary_trend_line)
        print("Trend Line - 1: ", self.trend_line_1)
        print("Trend Line - 2: ", self.trend_line_2)
        print("Trend Line - 3: ", self.trend_line_3)
        print("No Trend Zone - Middle: ", self.no_trend_zone_middle_line)
        print("Long Signal: ", self.long_signal_candle, "Short Signal: ", self.short_signal_candle)
        # print("Last Candle High:",np.array(high)[-2])
        # print("Higher Order:", round(np.array(high)[-2]+(np.array(high)[-2] * above_or_below_wick/100),2))
        # print("Last Candle Low:", np.array(low)[-2])
        # print("Lower Order:", round(np.array(low)[-2]-(np.array(low)[-2] * above_or_below_wick/100),2))

