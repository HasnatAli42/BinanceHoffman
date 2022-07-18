from datetime import datetime

from BinanceFuturesPy.futurespy import Client
from settings import SYMBOL, QNTY, Leverage, Decimal_point_price, above_or_below_wick, client, \
    position_quantity_any_direction, TIME_PERIOD, LIMIT, trailing_order_check, trailing_order_increase, TIME_SLEEP
import sqlite3 as sl
import requests
import numpy as np
import pandas as pd
import time


class TradingBot:

    def __init__(self, api_key, secret_key, stop_profit):
        self.LowestPrice = 1000000
        self.Highest_Price = 0
        self.order_sequence = 1
        self.api_key = api_key
        self.secret_key = secret_key
        self.stop_profit = stop_profit
        self.remaining_quantity = QNTY
        self.client = Client(api_key=api_key, sec_key=secret_key, testnet=False, symbol=SYMBOL, recv_window=30000)
        # self.client.API_URL = 'https://testnet.binance.vision/api'
        self.isOrderInProgress = False
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = False
        self.isOrderPlaced = False
        self.isLongOrderPlaced = False
        self.isShortOrderPlaced = False
        self.currency_price = None
        self.quantity = QNTY / 5
        self.profit = None
        self.firstRun = True
        self.low_price = 0
        self.high_price = 0
        self.place_order_price = 0
        self.trailing_order_price = 0
        self.new_place_order_price = 0
        self.newHoffmanSignalCheck = False
        self.isBreakEvenCalled = False
        self.LongHit = "LongHit"
        self.ShortHit = "ShortHit"
        self.take_profit = 1
        self.stop_loss = 0.4
        self.profit_ratio = 1
        self.order1 = ""
        self.order2 = ""
        self.shortCounter = 0
        self.LongCounter = 0

    def update_data_set(self, side):
        global total_wallet_balance, available_balance
        con = sl.connect('orders-executed.db')
        account_details = client.account_info()
        assets_details = account_details["assets"]
        for counter in assets_details:
            if counter["asset"] == "BUSD":
                total_wallet_balance = counter["walletBalance"]
                available_balance = counter["availableBalance"]
        sql = f'INSERT INTO FUTURES_{SYMBOL}_HOFFMAN (order_sequence,  Current_eth_price,' \
              'Etherium_quantity,' \
              'Remaining_quantity,LeverageTaken,TotalWalletBalance,AvailableBalance,' \
              'OrderFee,Method_applied,' \
              'Usd_used,HighestPrice,LowestPrice,OrderPrice,TakeProfitPrice,StopLossPrice, Time, Order1, ' \
              'Order2) values(?,?,?,?,?,?,' \
              '?,?,?,?,?,?,?,?,?,' \
              '?,?,?) '
        data = [
            (str(self.order_sequence)), (str(self.currency_price)),
            (str(QNTY)),
            (str(self.remaining_quantity)), (str(Leverage)),
            (str(total_wallet_balance)),
            (str(available_balance)), (str(round(float(self.currency_price * QNTY * 0.023 / 100), 6))), (str(side)),
            (str(round(float(self.currency_price * QNTY), 6))), (str(self.Highest_Price)), (str(self.LowestPrice)),
            (str(self.place_order_price)), (str(float(
                self.place_order_price + (self.place_order_price * self.take_profit / 100)))), (float(
                self.place_order_price - (self.place_order_price * self.stop_loss / 100))), (str(datetime.now())),
            (str(self.order1)), (str(self.order2)),
        ]
        with con:
            con.execute(sql, data)
            con.commit()
        self.Highest_Price = 0
        self.LowestPrice = 1000000
        self.order1 = ""
        self.order2 = ""

    def write_to_file(self):
        file = open(f'{SYMBOL}_is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.write("\n" + str(self.isOrderPlaced))
        file.write("\n" + str(self.isLongOrderPlaced))
        file.write("\n" + str(self.isShortOrderPlaced))
        file.write("\n" + str(self.newHoffmanSignalCheck))
        file.write("\n" + str(self.order_sequence))
        file.write("\n" + str(self.high_price))
        file.write("\n" + str(self.low_price))
        file.write("\n" + str(self.place_order_price))
        file.write("\n" + str(self.take_profit))
        file.write("\n" + str(self.stop_loss))
        file.write("\n" + str(self.trailing_order_price))
        file.close()

    def trailing_stop_loss_order(self, stop_loss_price):
        if position_quantity_any_direction() > 0:
            self.order2 = client.new_order(symbol=SYMBOL, orderType="STOP_MARKET", quantity=QNTY, side="SELL",
                                           stopPrice=round(stop_loss_price, Decimal_point_price),
                                           reduceOnly=True)
            if str(self.order2).find("code") >= 0:
                if self.order2["code"] == -2021:
                    self.order2 = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
                    self.LongHit = "LongHit2021"

        elif position_quantity_any_direction() < 0:
            self.order2 = client.new_order(symbol=SYMBOL, orderType="STOP_MARKET", quantity=QNTY, side="BUY",
                                           stopPrice=round(stop_loss_price, Decimal_point_price),
                                           reduceOnly=True)
            if str(self.order2).find("code") >= 0:
                if self.order2["code"] == -2021:
                    self.order2 = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
                    self.ShortHit = "ShortHit2021"

    def place_long_order(self, long):
        client.cancel_all_open_orders(SYMBOL)
        self.order1 = client.new_order(symbol=SYMBOL, orderType="STOP", quantity=QNTY, side="BUY",
                                       price=round((long + ((long * above_or_below_wick) / 100)), Decimal_point_price),
                                       stopPrice=round(long, Decimal_point_price), reduceOnly=False,
                                       timeInForce='GTC')
        self.isOrderPlaced = True
        self.isLongOrderPlaced = True
        self.isShortOrderPlaced = False
        return self.order1

    def cancel_executed_orders(self):
        client.cancel_all_open_orders(SYMBOL)
        self.remaining_quantity = position_quantity_any_direction()
        if self.remaining_quantity > 0:
            self.order1 = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
        elif self.remaining_quantity < 0:
            self.order1 = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")

    def place_short_order(self, short):
        client.cancel_all_open_orders(SYMBOL)
        self.order1 = client.new_order(symbol=SYMBOL, orderType="STOP", quantity=QNTY, side="SELL",
                                       price=round((short - ((short * above_or_below_wick) / 100)),
                                                   Decimal_point_price),
                                       stopPrice=round(short, Decimal_point_price),
                                       reduceOnly=False, timeInForce='GTC')
        self.isOrderPlaced = True
        self.isLongOrderPlaced = False
        self.isShortOrderPlaced = True
        return self.order1

    def place_in_progress_order_limits(self):
        if position_quantity_any_direction() > 0:
            self.order1 = client.new_order(symbol=SYMBOL, orderType="LIMIT", quantity=QNTY, side="SELL",
                                           price=round((
                                                   self.place_order_price + (self.place_order_price * self.take_profit /
                                                                             100)), Decimal_point_price),
                                           reduceOnly=False, timeInForce='GTC')
            self.order2 = client.new_order(symbol=SYMBOL, orderType="STOP_MARKET", quantity=QNTY, side="SELL",
                                           stopPrice=round(
                                               (self.place_order_price - (self.place_order_price * self.stop_loss /
                                                                          100)),
                                               Decimal_point_price),
                                           reduceOnly=True)
            if str(self.order2).find("code") >= 0:
                if self.order2["code"] == -2021:
                    self.order2 = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
                    self.LongHit = "LongHit2021"

        elif position_quantity_any_direction() < 0:
            self.order1 = client.new_order(symbol=SYMBOL, orderType="LIMIT", quantity=QNTY, side="BUY",
                                           price=round(
                                               (self.place_order_price - (self.place_order_price * self.take_profit /
                                                                          100)), Decimal_point_price),
                                           reduceOnly=False, timeInForce='GTC')
            self.order2 = client.new_order(symbol=SYMBOL, orderType="STOP_MARKET", quantity=QNTY, side="BUY",
                                           stopPrice=round(
                                               (self.place_order_price + (self.place_order_price * self.stop_loss /
                                                                          100)),
                                               Decimal_point_price),
                                           reduceOnly=True)
            if str(self.order2).find("code") >= 0:
                if self.order2["code"] == -2021:
                    self.order2 = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
                    self.ShortHit = "ShortHit2021"

    def place_trailing_stop_loss(self):
        if position_quantity_any_direction() > 0:
            if self.currency_price > self.trailing_order_price + (self.trailing_order_price *(trailing_order_check/100)):
                self.trailing_order_price = self.trailing_order_price + (self.trailing_order_price * (trailing_order_increase/100))
                self.trailing_stop_loss_order(self.trailing_order_price)
        elif position_quantity_any_direction() < 0:
            if self.currency_price < self.trailing_order_price + (self.trailing_order_price *(trailing_order_check/100)):
                self.trailing_order_price = self.trailing_order_price - (self.trailing_order_price * (trailing_order_increase/100))
                self.trailing_stop_loss_order(self.trailing_order_price)

    def calculate_ema(self, prices, days, smoothing=2):
        ema = [sum(prices[:days]) / days]
        for price in prices[days:]:
            ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
        return ema

    def tr_calculation(self, high, low, close):
        high_low = high - low
        high_close = np.abs(high - np.array(close)[-1])
        low_close = np.abs(low - np.array(close)[-1])
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return np.array(true_range)

    def calcluate_rma(self, rma_data, rmaPeriod):
        alpha = 1 / rmaPeriod
        rma = []
        for i in range(len(rma_data)):
            rma_cal = ((alpha * rma_data[i - 1]) + ((1 - alpha) * rma_data[i]))
            rma.append(rma_cal)
        return rma

    def upper_and_lower_trend_zone_line(self, high, low, close):
        rma_data = self.tr_calculation(high, low, close)
        rma = self.calcluate_rma(rma_data, 35)[-1]
        k = self.calculate_ema(close, 35)[-1]
        trend_zone_upper = k + rma * 0.5
        return trend_zone_upper

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

    def calcSma(self, data, smaPeriod):
        j = next(i for i, x in enumerate(data) if x is not None)
        our_range = range(len(data))[j + smaPeriod - 1:]
        empty_list = [None] * (j + smaPeriod - 1)
        sub_result = [np.mean(data[i - smaPeriod + 1: i + 1]) for i in our_range]

        return np.array(empty_list + sub_result)

    def get_data(self):
        url = "https://fapi.binance.com/fapi/v1/klines?symbol={}&interval={}&limit={}".format(SYMBOL, TIME_PERIOD,
                                                                                              LIMIT)
        res = requests.get(url)
        closed_data = []
        for each in res.json():
            closed_data.append(each)
        data = pd.DataFrame(data=closed_data).iloc[:, 1: 5]
        data.columns = ["open", "high", "low", "close"]
        data["open"] = pd.to_numeric(data["open"])
        data["high"] = pd.to_numeric(data["high"])
        data["low"] = pd.to_numeric(data["low"])
        data["close"] = pd.to_numeric(data["close"])
        return data["open"], data["high"], data["low"], data["close"]

    def get_price(self):
        try:
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
        except Exception as e:
            time.sleep(180)
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
        res = requests.get(url)
        return float(res.json()['price'])

    def time_dot_round(self, TIME_PERIOD):
        print("Time dot Sleep Started", datetime.now())
        candle_time = int(TIME_PERIOD.replace("m", ""))
        candle_time_seconds = candle_time * 60
        minute = datetime.now().minute
        second = datetime.now().second
        micro = datetime.now().microsecond
        time_for_next_candle = ((minute % candle_time) * 60) + second + (micro / 1000000)
        time.sleep(candle_time_seconds - time_for_next_candle + 2)
        print("Time dot Sleep End", datetime.now())

    def executed_order_on_wick_check(self):
        self.time_dot_round(TIME_PERIOD=TIME_PERIOD)
        time.sleep(TIME_SLEEP)
        start, high, low, close = self.get_data()
        if self.isLongOrderInProgress:
            if high[-2] > self.place_order_price > close[-2]:
                self.cancel_executed_orders()
                self.update_data_set(side="LongHitWick")
        elif self.isShortOrderInProgress:
            if low[-2] < self.place_order_price < close[-2]:
                self.cancel_executed_orders()
                self.update_data_set(side="ShortHitWick")







