import os
import time
from datetime import datetime
import pandas as pd
import requests
import numpy as np
import talib
import sqlite3 as sl
from numpy.core.defchararray import strip
from BinanceFuturesPy.futurespy import Client
from config_usama import api_key, api_secret


#When changing symbol change decimal points
SYMBOL = "FTMBUSD"
Decimal_point_price = 4
Decimal_point_qty = 0

con = sl.connect('orders-executed.db')
with con:
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS FUTURES_{SYMBOL}_HOFFMAN  (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_sequence TEXT,
            Current_eth_price TEXT,
            Etherium_quantity TEXT,
            Remaining_quantity TEXT,
            LeverageTaken TEXT,
            TotalWalletBalance TEXT,
            AvailableBalance TEXT,
            OrderFee TEXT,
            Method_applied TEXT,
            Usd_used TEXT,
            LowestPrice TEXT,
            HighestPrice TEXT,
            OrderPrice TEXT,
            TakeProfitPrice TEXT,
            StopLossPrice TEXT,
            Time TEXT,
            Order1 TEXT,
            Order2 TEXT
        );
    """)

Dollars = 20
TIME_PERIOD = "3m"
LIMIT = "300"
TIME_SLEEP = 1
Leverage = 1
above_or_below_wick = 0.1
client = Client(api_key=api_key, sec_key=api_secret, testnet=False, symbol=SYMBOL, recv_window=30000)
client.change_leverage(Leverage)




def dollors_to_cryto_quantiy(quantity):
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
    except Exception as e:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
    res = requests.get(url)
    return round((quantity / float(res.json()['price'])), Decimal_point_qty)


QNTY = dollors_to_cryto_quantiy(Dollars)
print(QNTY)


def position_quantity():
    posInfo = client.position_info()
    for counter in posInfo:
        if counter["symbol"] == SYMBOL:
            quantity = abs(float(counter["positionAmt"]))
            return quantity


def position_quantity_any_direction():
    posInfo = client.position_info()
    for counter in posInfo:
        if counter["symbol"] == SYMBOL:
            quantity = float(counter["positionAmt"])
            return quantity


def position_info():
    posInfo = client.position_info()

    for counter in posInfo:
        if counter["symbol"] == SYMBOL:
            print(counter)
            return counter


def take_profit_market():
    posInfo = position_info()
    entry_price = float(posInfo["entryPrice"])
    percent = (0.5 * entry_price) / 100
    return percent


def entry_price():
    posInfo = position_info()
    entry_price = float(posInfo["entryPrice"])
    return entry_price


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
        self.new_place_order_price = 0
        self.newHoffmanSignalCheck = False
        self.LongHit = "LongHit"
        self.ShortHit = "ShortHit"
        self.take_profit = 1
        self.stop_loss = 0.4
        self.profit_ratio = 1
        self.order1 = ""
        self.order2 = ""

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
        file.close()

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
        candle_time = int(TIME_PERIOD.replace("m", ""))
        candle_time_seconds = candle_time * 60
        minute = datetime.now().minute
        second = datetime.now().second
        micro = datetime.now().microsecond
        time_for_next_candle = ((minute % candle_time) * 60) + second + (micro / 1000000)
        time.sleep(candle_time_seconds - time_for_next_candle + 2)


def main(trade_bot_obj: TradingBot):
    last_slow_speed_line = None
    last_fast_primary_trend_line = None
    while True:
        open, high, low, close = trading_bot_obj.get_data()
        # print(np.array(low)[-2])
        numpy_close = np.array(close)
        slow_speed_line = trading_bot_obj.calcSma(numpy_close, 5)[-1]
        fast_primary_trend_line = talib.EMA(numpy_close, 18)[-1]
        trend_line_1 = trading_bot_obj.calcSma(numpy_close, 50)[-1]
        trend_line_2 = trading_bot_obj.calcSma(numpy_close, 89)[-1]
        trend_line_3 = talib.EMA(numpy_close, 144)[-1]
        no_trend_zone_middle_line = talib.EMA(numpy_close, 35)[-1]
        # no_trend_zone_upper_line = trading_bot_obj.upper_and_lower_trend_zone_line(high, low, close) + 2.6
        long_signal_candle, short_signal_candle = trading_bot_obj.trigger_candle_45_per(np.array(open)[-2],
                                                                                        np.array(high)[-2],
                                                                                        np.array(low)[-2],
                                                                                        np.array(close)[-2], 45)
        trade_bot_obj.currency_price = trade_bot_obj.get_price()

        if trade_bot_obj.Highest_Price < trade_bot_obj.currency_price:
            trade_bot_obj.Highest_Price = trade_bot_obj.currency_price
        if trade_bot_obj.LowestPrice > trade_bot_obj.currency_price:
            trade_bot_obj.LowestPrice = trade_bot_obj.currency_price

        if trade_bot_obj.firstRun:
            trade_bot_obj.firstRun = False
            print("\n--------- Currency ---------")
            print(SYMBOL, ":", trade_bot_obj.currency_price)
            print("----------------------------")
            print("\n************** Strategy Result First Run ***********")
            print("Slow Speed Line: ", slow_speed_line)
            print("Fast Primary Trend Line: ", fast_primary_trend_line)
            print("Trend Line - 1: ", trend_line_1)
            print("Trend Line - 2: ", trend_line_2)
            print("Trend Line - 3: ", trend_line_3)
            print("No Trend Zone - Middle: ", no_trend_zone_middle_line)
            print("Long Signal: ", long_signal_candle, "Short Signal: ", short_signal_candle)
            # print("Last Candle High:",np.array(high)[-2])
            # print("Higher Order:", round(np.array(high)[-2]+(np.array(high)[-2] * above_or_below_wick/100),2))
            # print("Last Candle Low:", np.array(low)[-2])
            # print("Lower Order:", round(np.array(low)[-2]-(np.array(low)[-2] * above_or_below_wick/100),2))

        else:
            if trade_bot_obj.isOrderPlaced and trade_bot_obj.isLongOrderPlaced:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("\n************** Strategy Result Long Placed at: ",
                      trade_bot_obj.high_price + (trade_bot_obj.high_price * above_or_below_wick / 100), " ***********")
                print(f"Take Profit {trade_bot_obj.take_profit} |-------| Stop Loss {trade_bot_obj.stop_loss}")
                if not long_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = True
                if long_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.high_price = np.array(high)[-2]
                    trade_bot_obj.new_place_order_price = round(
                        trade_bot_obj.high_price + (trade_bot_obj.high_price * above_or_below_wick / 100),
                        Decimal_point_price)
                    if trade_bot_obj.new_place_order_price != trade_bot_obj.place_order_price:
                        client.cancel_all_open_orders(SYMBOL)
                        trade_bot_obj.place_order_price = trade_bot_obj.new_place_order_price
                        trade_bot_obj.place_long_order(long=trade_bot_obj.place_order_price)
                        trade_bot_obj.stop_loss = ((trade_bot_obj.place_order_price - fast_primary_trend_line) / \
                                                   trade_bot_obj.place_order_price) * 100
                        trade_bot_obj.take_profit = trading_bot_obj.stop_loss * trade_bot_obj.profit_ratio
                        trade_bot_obj.update_data_set("LongUpdated")
                        trade_bot_obj.write_to_file()

                if position_quantity() > 0:
                    print("Order Executed Successfully")
                    trade_bot_obj.isOrderPlaced = False
                    trade_bot_obj.isLongOrderPlaced = False
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.isOrderInProgress = True
                    trade_bot_obj.isLongOrderInProgress = True
                    trade_bot_obj.update_data_set("LongExecuted")
                    trade_bot_obj.place_in_progress_order_limits()
                    trade_bot_obj.write_to_file()
                if slow_speed_line < fast_primary_trend_line:
                    print("Order Cancelled Successfully")
                    client.cancel_all_open_orders(SYMBOL)
                    trade_bot_obj.isOrderPlaced = False
                    trade_bot_obj.isLongOrderPlaced = False
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.update_data_set("LongCancelled")
                    trade_bot_obj.write_to_file()
            elif trade_bot_obj.isOrderPlaced and trade_bot_obj.isShortOrderPlaced:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("\n************** Strategy Result Short Placed at: ", trade_bot_obj.place_order_price,
                      " ***********")
                print(f"Take Profit {trade_bot_obj.take_profit} |-------| Stop Loss {trade_bot_obj.stop_loss}")
                if not short_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = True
                if short_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.low_price = np.array(low)[-2]
                    trade_bot_obj.new_place_order_price = round(
                        trade_bot_obj.low_price - (trade_bot_obj.low_price * above_or_below_wick / 100),
                        Decimal_point_price)
                    if trade_bot_obj.new_place_order_price != trade_bot_obj.place_order_price:
                        client.cancel_all_open_orders(SYMBOL)
                        trade_bot_obj.place_order_price = trade_bot_obj.new_place_order_price
                        trade_bot_obj.place_short_order(short=trade_bot_obj.place_order_price)
                        trade_bot_obj.stop_loss = (fast_primary_trend_line - trade_bot_obj.place_order_price) / \
                                                  trade_bot_obj.place_order_price * 100
                        trade_bot_obj.take_profit = trading_bot_obj.stop_loss * trade_bot_obj.profit_ratio
                        trade_bot_obj.update_data_set("ShortUpdated")
                        trade_bot_obj.write_to_file()
                if position_quantity() > 0:
                    print("Order Executed Successfully")
                    trade_bot_obj.isOrderPlaced = False
                    trade_bot_obj.isShortOrderPlaced = False
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.isOrderInProgress = True
                    trade_bot_obj.isShortOrderInProgress = True
                    trade_bot_obj.update_data_set("ShortExecuted")
                    trade_bot_obj.place_in_progress_order_limits()
                    trade_bot_obj.write_to_file()
                if slow_speed_line > fast_primary_trend_line:
                    print("Order Cancelled Successfully")
                    client.cancel_all_open_orders(SYMBOL)
                    trade_bot_obj.isOrderPlaced = False
                    trade_bot_obj.isShortOrderPlaced = False
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.update_data_set("ShortCancelled")
                    trade_bot_obj.write_to_file()
            elif trade_bot_obj.isOrderInProgress and trade_bot_obj.isLongOrderInProgress:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("Take Profit:",
                      trade_bot_obj.place_order_price + (trade_bot_obj.place_order_price * trade_bot_obj.take_profit
                                                         / 100))
                print("Stop Loss:",
                      trade_bot_obj.place_order_price - (trade_bot_obj.place_order_price * trade_bot_obj.stop_loss /
                                                         100))
                print("\n************** Strategy Result Long In Progress ***********")
                if position_quantity() == 0:
                    client.cancel_all_open_orders(SYMBOL)
                    if trade_bot_obj.LongHit == "LongHit" and trade_bot_obj.currency_price > trade_bot_obj.place_order_price:
                        trade_bot_obj.LongHit = "LongHitProfit"
                    elif trade_bot_obj.LongHit == "LongHit" and trade_bot_obj.currency_price < trade_bot_obj.place_order_price:
                        trade_bot_obj.LongHit = "LongHitLoss"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isLongOrderInProgress = False
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.LongHit)
                    trade_bot_obj.LongHit = "LongHit"
                    trade_bot_obj.write_to_file()
                if slow_speed_line < fast_primary_trend_line:
                    print("Order In-Progress Cancelled Successfully")
                    trade_bot_obj.LongHit = "LongHitCrossing"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isLongOrderInProgress = False
                    trade_bot_obj.cancel_executed_orders()
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.LongHit)
                    trade_bot_obj.LongHit = "LongHit"
                    trade_bot_obj.write_to_file()
                if not trade_bot_obj.isOrderInProgress and not trade_bot_obj.isLongOrderInProgress:
                    print("Long Order Sleep Time is Called")
                    trade_bot_obj.update_data_set("sleep started")
                    trade_bot_obj.time_dot_round(TIME_PERIOD)
                    trade_bot_obj.update_data_set("sleep ended")
            elif trade_bot_obj.isOrderInProgress and trade_bot_obj.isShortOrderInProgress:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("Take Profit:",
                      trade_bot_obj.place_order_price - (trade_bot_obj.place_order_price * trade_bot_obj.take_profit
                                                         / 100))
                print("Stop Loss:",
                      trade_bot_obj.place_order_price + (trade_bot_obj.place_order_price * trade_bot_obj.stop_loss /
                                                         100))
                print("\n************** Strategy Result Short In Progress ***********")
                if position_quantity() == 0:
                    client.cancel_all_open_orders(SYMBOL)
                    if trade_bot_obj.ShortHit == "ShortHit" and trade_bot_obj.currency_price < trade_bot_obj.place_order_price:
                        trade_bot_obj.ShortHit = "ShortHitProfit"
                    elif trade_bot_obj.ShortHit == "ShortHit" and trade_bot_obj.currency_price > trade_bot_obj.place_order_price:
                        trade_bot_obj.ShortHit = "ShortHitLoss"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isShortOrderInProgress = False
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.ShortHit)
                    trade_bot_obj.ShortHit = "ShortHit"
                    trade_bot_obj.write_to_file()
                if slow_speed_line > fast_primary_trend_line:
                    print("Short Order In-Progress Cancelled Successfully")
                    trade_bot_obj.ShortHit = "ShortHitCrossing"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isShortOrderInProgress = False
                    trade_bot_obj.cancel_executed_orders()
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.ShortHit)
                    trade_bot_obj.ShortHit = "ShortHit"
                    trade_bot_obj.write_to_file()
                if not trade_bot_obj.isOrderInProgress and not trade_bot_obj.isShortOrderInProgress:
                    print("Short Order Sleep Time is Called")
                    trade_bot_obj.update_data_set("sleep started")
                    trade_bot_obj.time_dot_round(TIME_PERIOD)
                    trade_bot_obj.update_data_set("sleep ended")
            elif not trade_bot_obj.isOrderInProgress and not trade_bot_obj.isOrderPlaced:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("----------------------------")
                print("\n************** Strategy Result Getting First Order ***********")
                if slow_speed_line > fast_primary_trend_line:
                    if trend_line_1 >= fast_primary_trend_line or trend_line_2 >= fast_primary_trend_line or trend_line_3 >= fast_primary_trend_line or no_trend_zone_middle_line >= fast_primary_trend_line:
                        print("Long Crossed But lines in between")
                    else:
                        print("Long Crossed looking for Hoffman Long signal wicked candle")
                        print("Hoffman Long Signal:", long_signal_candle)
                        if long_signal_candle:
                            trade_bot_obj.high_price = np.array(high)[-2]
                            trade_bot_obj.place_order_price = round(
                                trade_bot_obj.high_price + (trade_bot_obj.high_price * above_or_below_wick / 100),
                                Decimal_point_price)
                            trade_bot_obj.stop_loss = ((trade_bot_obj.place_order_price - fast_primary_trend_line) / \
                                                       trade_bot_obj.place_order_price) * 100
                            trade_bot_obj.take_profit = trading_bot_obj.stop_loss * trade_bot_obj.profit_ratio
                            trade_bot_obj.isOrderPlaced = True
                            trade_bot_obj.isLongOrderPlaced = True
                            trade_bot_obj.place_long_order(long=trade_bot_obj.place_order_price)
                            trade_bot_obj.update_data_set("LongOrderPlaced")
                            trade_bot_obj.write_to_file()
                else:
                    if trend_line_1 <= fast_primary_trend_line or trend_line_2 <= fast_primary_trend_line or trend_line_3 <= fast_primary_trend_line or no_trend_zone_middle_line <= fast_primary_trend_line:
                        print("Short Crossed But lines in between")
                    else:
                        print("Short Crossed looking for Hoffman Short signal wicked candle")
                        print("Hoffman Short Signal:", short_signal_candle)
                        if short_signal_candle:
                            trade_bot_obj.low_price = np.array(low)[-2]
                            trade_bot_obj.place_order_price = round(
                                trade_bot_obj.low_price - (trade_bot_obj.low_price * above_or_below_wick / 100),
                                Decimal_point_price)
                            trade_bot_obj.stop_loss = (fast_primary_trend_line - trade_bot_obj.place_order_price) / \
                                                      trade_bot_obj.place_order_price * 100
                            trade_bot_obj.take_profit = trading_bot_obj.stop_loss * trade_bot_obj.profit_ratio
                            trade_bot_obj.isOrderPlaced = True
                            trade_bot_obj.isShortOrderPlaced = True
                            trade_bot_obj.place_short_order(short=trade_bot_obj.place_order_price)
                            trade_bot_obj.update_data_set("ShortOrderPlaced")
                            trade_bot_obj.write_to_file()

        last_slow_speed_line = slow_speed_line
        last_fast_primary_trend_line = fast_primary_trend_line
        time.sleep(TIME_SLEEP)


if __name__ == "__main__":
    trading_bot_obj = TradingBot(api_key=api_key, secret_key=api_secret, stop_profit=0.5)
    while True:
        try:
            if os.path.exists(f'{SYMBOL}_is_order_in_progress.txt'):
                file = open(f'{SYMBOL}_is_order_in_progress.txt', 'r')
                x, y, z, xx, yy, zz, xxx, a, b, c, d, e, f = file.readlines()
                file.close()
                x = strip(x)
                y = strip(y)
                z = strip(z)
                xx = strip(xx)
                yy = strip(yy)
                zz = strip(zz)
                xxx = strip(xxx)
                a = strip(a)
                b = strip(b)
                c = strip(c)
                d = strip(d)
                e = strip(e)
                f = strip(f)
                if x == "True":
                    trading_bot_obj.isOrderInProgress = True
                if y == "True":
                    trading_bot_obj.isLongOrderInProgress = True
                if z == "True":
                    trading_bot_obj.isShortOrderInProgress = True
                if xx == "True":
                    trading_bot_obj.isOrderPlaced = True
                if yy == "True":
                    trading_bot_obj.isLongOrderPlaced = True
                if zz == "True":
                    trading_bot_obj.isShortOrderPlaced = True
                if xxx == "True":
                    trading_bot_obj.newHoffmanSignalCheck = True
                trading_bot_obj.order_sequence = int(a)
                trading_bot_obj.high_price = float(b)
                trading_bot_obj.low_price = float(c)
                trading_bot_obj.place_order_price = float(d)
                trading_bot_obj.take_profit = float(e)
                trading_bot_obj.stop_loss = float(f)
                main(trading_bot_obj)
            else:
                main(trading_bot_obj)
        except Exception as e:
            print(e)
            try:
                time.sleep(20)
            except Exception as e:
                print(e)
                time.sleep(10)
