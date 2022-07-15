import os
import time
from datetime import datetime
import requests
import numpy as np
import talib
from binance.client import Client as Client1  # importing client
import sqlite3 as sl

from numpy import double
from numpy.core.defchararray import strip

from BinanceFuturesPy.futurespy import Client

from config import api_key, api_secret

con = sl.connect('orders-executed.db')
with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS FUTURES_ETH  (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_sequence TEXT,
            Current_eth_price TEXT,
            Current_ema_higher TEXT,
            Current_ema_lower TEXT,
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
            Time TEXT
        );
    """)


with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS EMA_DIFFERENCE  (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Ema_Difference TEXT,
            Method_applied TEXT,
            Time TEXT
        );
    """)


client1 = Client1(api_key, api_secret)
# client.API_URL = 'https://testnet.binance.vision/api'
SYMBOL = "ETHUSDT"
TIME_PERIOD = "1m"
LIMIT = "1000"
Quantity = 0.005
Leverage = 1
QNTY = Quantity * Leverage
EMA_Crossing_Difference = 0.4
EMA_Positive = 10
EMA_Negative = 20
client = Client(api_key=api_key, sec_key=api_secret, testnet=False, symbol=SYMBOL, recv_window=30000)
client.change_leverage(Leverage)


# client.cancel_all_open_orders(SYMBOL)
# print(client.current_open_orders())
# client.cancel_order(SYMBOL,"8389765519821480652", True)
# order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")

# print(order)
# order_Sl = client.new_order(symbol=SYMBOL, orderType="STOP_MARKET", quantity=QNTY, side="BUY", stopPrice=int(4000), reduceOnly=True)
# order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY, side="BUY",
#                             stopPrice=int(3525), reduceOnly=True)


# order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
# order_Sl = client.new_order(symbol=SYMBOL, orderType="STOP_MARKET", quantity=QNTY, side="SELL",stopPrice=int(3000), reduceOnly=True)
# print("Spot Client :", client1.get_account())
# print("Futures Client :", client.account_info())


def position_quantity():
    posInfo = client.position_info()
    for counter in posInfo:
        if counter["symbol"] == SYMBOL:
            quantity = abs(float(counter["positionAmt"]))
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
    percent = (0.12 * entry_price) / 100
    return percent


def entry_price():
    posInfo = position_info()
    entry_price = float(posInfo["entryPrice"])
    return entry_price


class TradingBot:

    def __init__(self, api_key, secret_key, stop_profit):
        self.api_key = api_key
        self.secret_key = secret_key
        self.stop_profit = stop_profit
        self.remaining_quantity = 0
        self.order_sequence = 0
        self.isOrderToBeExecuted = False
        self.isCrossingConfirmed = False
        self.client = Client(api_key=api_key, sec_key=secret_key, testnet=False, symbol=SYMBOL, recv_window=30000)
        # self.client.API_URL = 'https://testnet.binance.vision/api'
        self.isOrderInProgress = False
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = False
        self.currency_price = None
        self.quantity = QNTY / 5
        self.profit = None
        self.firstRun = True
        self.Highest_Price = 0
        self.LowestPrice = 10000
        self.current_trade_status = "Strategy Result First Run"
        self.ema_positive = 0.0
        self.ema_negative = 0.0
        self.ema_difference = []

    def buy_order_without_any_in_progress(self):
        con = sl.connect('orders-executed.db')
        client.cancel_all_open_orders(SYMBOL)
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = True
        self.isShortOrderInProgress = False
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.write("\n" + str(self.order_sequence))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY, side="SELL",
                                    stopPrice=int((1 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((2 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((3 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((4 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((5 * take_profit) + order_entry_price), reduceOnly=True)
        return order

    def buy_order(self):
        con = sl.connect('orders-executed.db')
        client.cancel_all_open_orders(SYMBOL)
        self.remaining_quantity = position_quantity()
        if self.remaining_quantity > 0:
            order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=self.remaining_quantity, side="BUY")
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = True
        self.isShortOrderInProgress = False
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.write("\n" + str(self.order_sequence))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY, side="SELL",
                                    stopPrice=int((1 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((2 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((3 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((4 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
        #                             stopPrice=int((5 * take_profit) + order_entry_price), reduceOnly=True)
        return order

    def sell_order_without_any_in_progress(self):
        con = sl.connect('orders-executed.db')
        client.cancel_all_open_orders(SYMBOL)
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = True
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.write("\n" + str(self.order_sequence))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY, side="BUY",
                                    stopPrice=int(-(1 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(2 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(3 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(4 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(5 * take_profit) + order_entry_price), reduceOnly=True)
        return order

    def sell_order(self):
        con = sl.connect('orders-executed.db')
        client.cancel_all_open_orders(SYMBOL)
        self.remaining_quantity = position_quantity()
        if self.remaining_quantity > 0:
            order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=self.remaining_quantity, side="SELL")
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = True
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.write("\n" + str(self.order_sequence))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY, side="BUY",
                                    stopPrice=int(-(1 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(2 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(3 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(4 * take_profit) + order_entry_price), reduceOnly=True)
        # order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
        #                             stopPrice=int(-(5 * take_profit) + order_entry_price), reduceOnly=True)

        return order

    def update_ema_difference(self, side):
        sql = 'INSERT INTO EMA_DIFFERENCE (Ema_Difference, Method_applied, Time) values(?,?,?)'
        data = [
            (str(self.ema_difference)), (str(side)), (str(datetime.now())),
        ]
        with con:
            con.execute(sql, data)
            con.commit()

    def update_data_set(self, side):
        account_details = client.account_info()
        total_wallet_balance = account_details["totalWalletBalance"]
        available_balance = account_details["availableBalance"]
        sql = 'INSERT INTO FUTURES_ETH (order_sequence, Current_eth_price, Current_ema_higher, Current_ema_lower,' \
              'Etherium_quantity,' \
              'Remaining_quantity,LeverageTaken,TotalWalletBalance,AvailableBalance,' \
              'OrderFee,Method_applied,' \
              'Usd_used,HighestPrice,LowestPrice,Time) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '
        data = [
            (str(self.order_sequence)), (str(self.currency_price)), (str('{0:.8g}'.format(self.ema_positive))), (str('{0:.8g}'.format(self.ema_negative))),
            (str(QNTY)),
            (str(self.remaining_quantity)), (str(Leverage)),
            (str(total_wallet_balance)),
            (str(available_balance)), (str(round(float(self.currency_price * QNTY * 0.08 / 100), 6))), (str(side)),
            (str(round(float(self.currency_price * QNTY), 6))), (str(self.Highest_Price)), (str(self.LowestPrice)),
            (str(datetime.now())),
        ]
        with con:
            con.execute(sql, data)
            con.commit()
        self.Highest_Price = 0
        self.LowestPrice = 1000000

    def get_data(self):
        try:
            url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(SYMBOL, TIME_PERIOD,
                                                                                                LIMIT)
        except Exception as e:
            time.sleep(180)
            url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(SYMBOL, TIME_PERIOD,
                                                                                                LIMIT)
        res = requests.get(url)
        closed_data = []
        for each in res.json():
            closed_data.append(float(each[4]))
        return np.array(closed_data)

    def get_price(self):
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        except Exception as e:
            time.sleep(180)
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
        res = requests.get(url)
        return float(res.json()['price'])


def main(trade_bot_obj: TradingBot):
    last_ema_9 = None
    last_ema_26 = None
    while True:
        closing_data = trade_bot_obj.get_data()
        trade_bot_obj.currency_price = trade_bot_obj.get_price()
        trade_bot_obj.ema_positive = talib.EMA(closing_data, EMA_Positive)[-1]
        trade_bot_obj.ema_negative = talib.EMA(closing_data, EMA_Negative)[-1]
        rsi = talib.RSI(closing_data, 14)[-1]


        if trade_bot_obj.Highest_Price < trade_bot_obj.currency_price:
            trade_bot_obj.Highest_Price = trade_bot_obj.currency_price
        if trade_bot_obj.LowestPrice > trade_bot_obj.currency_price:
            trade_bot_obj.LowestPrice = trade_bot_obj.currency_price

        print("\n--------- Currency ---------")
        print(SYMBOL, ":", trade_bot_obj.currency_price)
        print("----------------------------")
        print("\n************** ", trade_bot_obj.current_trade_status, " ***********")
        print("EMA-9 Strategy : ", trade_bot_obj.ema_positive)
        print("EMA-26 Signal  : ", trade_bot_obj.ema_negative)
        print("RSI Strategy   : ", rsi)
        # trade_bot_obj.buy_order_without_any_in_progress()
        # trade_bot_obj.sell_order()
        # trade_bot_obj.buy_order()
        # trade_bot_obj.sell_order_without_any_in_progress()
        if trade_bot_obj.firstRun:
            trade_bot_obj.firstRun = False
        else:
            if trade_bot_obj.isOrderInProgress and trade_bot_obj.isLongOrderInProgress:
                trade_bot_obj.current_trade_status = "Strategy Result Long In Progress"
                trade_bot_obj.ema_difference.append(trade_bot_obj.ema_positive - trade_bot_obj.ema_negative)
                if trade_bot_obj.ema_negative > trade_bot_obj.ema_positive and last_ema_26:
                    if last_ema_26 < last_ema_9:
                        trade_bot_obj.isOrderToBeExecuted = True
                        while trade_bot_obj.isOrderToBeExecuted:
                            closing_data = trade_bot_obj.get_data()
                            trade_bot_obj.currency_price = trade_bot_obj.get_price()
                            trade_bot_obj.ema_positive = talib.EMA(closing_data, EMA_Positive)[-1]
                            trade_bot_obj.ema_negative = talib.EMA(closing_data, EMA_Negative)[-1]
                            print("\n************** Confirming Crossing ***********")
                            print("----------------------------")
                            print("\n************** ", trade_bot_obj.current_trade_status, " ***********")
                            print("EMA-9 Strategy : ", trade_bot_obj.ema_positive)
                            print("EMA-26 Signal  : ", trade_bot_obj.ema_negative)
                            if trade_bot_obj.ema_negative - trade_bot_obj.ema_positive > EMA_Crossing_Difference:
                                trade_bot_obj.isCrossingConfirmed = True
                                trade_bot_obj.isOrderToBeExecuted = False
                            elif trade_bot_obj.ema_positive > trade_bot_obj.ema_negative:
                                trade_bot_obj.isOrderToBeExecuted = False
                            time.sleep(5)
                        if trade_bot_obj.isCrossingConfirmed:
                            trade_bot_obj.isCrossingConfirmed = False
                            trade_bot_obj.sell_order()
                            trade_bot_obj.order_sequence += 1
                            trade_bot_obj.update_data_set("sell")
                            trade_bot_obj.update_ema_difference("buy")
                            trade_bot_obj.ema_difference.clear()
            elif trade_bot_obj.isOrderInProgress and trade_bot_obj.isShortOrderInProgress:
                trade_bot_obj.current_trade_status = "Strategy Result Short In Progress"
                trade_bot_obj.ema_difference.append(trade_bot_obj.ema_negative - trade_bot_obj.ema_positive)
                if trade_bot_obj.ema_positive > trade_bot_obj.ema_negative and last_ema_9:
                    if last_ema_9 < last_ema_26:
                        trade_bot_obj.isOrderToBeExecuted = True
                        while trade_bot_obj.isOrderToBeExecuted:
                            closing_data = trade_bot_obj.get_data()
                            trade_bot_obj.currency_price = trade_bot_obj.get_price()
                            trade_bot_obj.ema_positive = talib.EMA(closing_data, EMA_Positive)[-1]
                            trade_bot_obj.ema_negative = talib.EMA(closing_data, EMA_Negative)[-1]
                            print("\n************** Confirming Crossing ***********")
                            print("----------------------------")
                            print("\n************** ", trade_bot_obj.current_trade_status, " ***********")
                            print("EMA-9 Strategy : ", trade_bot_obj.ema_positive)
                            print("EMA-26 Signal  : ", trade_bot_obj.ema_negative)
                            if trade_bot_obj.ema_positive - trade_bot_obj.ema_negative > EMA_Crossing_Difference:
                                trade_bot_obj.isCrossingConfirmed = True
                                trade_bot_obj.isOrderToBeExecuted = False
                            elif trade_bot_obj.ema_negative > trade_bot_obj.ema_positive:
                                trade_bot_obj.isOrderToBeExecuted = False
                            time.sleep(5)
                        if trade_bot_obj.isCrossingConfirmed:
                            trade_bot_obj.isCrossingConfirmed = False
                            trade_bot_obj.buy_order()
                            trade_bot_obj.order_sequence += 1
                            trade_bot_obj.update_data_set("buy")
                            trade_bot_obj.update_ema_difference("sell")
                            trade_bot_obj.ema_difference.clear()
            elif not trade_bot_obj.isOrderInProgress:
                trade_bot_obj.current_trade_status = "Strategy Result Getting First Order"
                if trade_bot_obj.ema_negative > trade_bot_obj.ema_positive and last_ema_26:
                    if last_ema_26 < last_ema_9:
                        trade_bot_obj.isOrderToBeExecuted = True
                        while trade_bot_obj.isOrderToBeExecuted:
                            closing_data = trade_bot_obj.get_data()
                            trade_bot_obj.currency_price = trade_bot_obj.get_price()
                            trade_bot_obj.ema_positive = talib.EMA(closing_data, EMA_Positive)[-1]
                            trade_bot_obj.ema_negative = talib.EMA(closing_data, EMA_Negative)[-1]
                            print("\n************** Confirming Crossing ***********")
                            print("----------------------------")
                            print("\n************** ", trade_bot_obj.current_trade_status, " ***********")
                            print("EMA-9 Strategy : ", trade_bot_obj.ema_positive)
                            print("EMA-26 Signal  : ", trade_bot_obj.ema_negative)
                            if trade_bot_obj.ema_negative - trade_bot_obj.ema_positive > EMA_Crossing_Difference:
                                trade_bot_obj.isCrossingConfirmed = True
                                trade_bot_obj.isOrderToBeExecuted = False
                            elif trade_bot_obj.ema_positive > trade_bot_obj.ema_negative:
                                trade_bot_obj.isOrderToBeExecuted = False
                            time.sleep(5)
                        if trade_bot_obj.isCrossingConfirmed:
                            trade_bot_obj.isCrossingConfirmed = False
                            trade_bot_obj.sell_order_without_any_in_progress()
                            trade_bot_obj.order_sequence += 1
                            trade_bot_obj.update_data_set("sell")
                if trade_bot_obj.ema_positive > trade_bot_obj.ema_negative and last_ema_9:
                    if last_ema_9 < last_ema_26:
                        trade_bot_obj.isOrderToBeExecuted = True
                        while trade_bot_obj.isOrderToBeExecuted:
                            closing_data = trade_bot_obj.get_data()
                            trade_bot_obj.currency_price = trade_bot_obj.get_price()
                            trade_bot_obj.ema_positive = talib.EMA(closing_data, EMA_Positive)[-1]
                            trade_bot_obj.ema_negative = talib.EMA(closing_data, EMA_Negative)[-1]
                            print("\n************** Confirming Crossing ***********")
                            print("----------------------------")
                            print("\n************** ", trade_bot_obj.current_trade_status, " ***********")
                            print("EMA-9 Strategy : ", trade_bot_obj.ema_positive)
                            print("EMA-26 Signal  : ", trade_bot_obj.ema_negative)
                            if trade_bot_obj.ema_positive - trade_bot_obj.ema_negative > EMA_Crossing_Difference:
                                trade_bot_obj.isCrossingConfirmed = True
                                trade_bot_obj.isOrderToBeExecuted = False
                            elif trade_bot_obj.ema_negative > trade_bot_obj.ema_positive:
                                trade_bot_obj.isOrderToBeExecuted = False
                            time.sleep(5)
                        if trade_bot_obj.isCrossingConfirmed:
                            trade_bot_obj.isCrossingConfirmed = False
                            trade_bot_obj.buy_order_without_any_in_progress()
                            trade_bot_obj.order_sequence += 1
                            trade_bot_obj.update_data_set("buy")

        last_ema_9 = trade_bot_obj.ema_positive
        last_ema_26 = trade_bot_obj.ema_negative
        time.sleep(5)


if __name__ == "__main__":
    trading_bot_obj = TradingBot(api_key=api_key, secret_key=api_secret, stop_profit=0.5)
    while True:
        try:
            if os.path.exists("is_order_in_progress.txt"):
                file = open('is_order_in_progress.txt', 'r')
                x, y, z, a = file.readlines()
                file.close()
                x = strip(x)
                y = strip(y)
                z = strip(z)
                a = strip(a)
                if x == "True":
                    trading_bot_obj.isOrderInProgress = True
                if y == "True":
                    trading_bot_obj.isLongOrderInProgress = True
                if z == "True":
                    trading_bot_obj.isShortOrderInProgress = True
                trading_bot_obj.order_sequence = int(a)
                main(trading_bot_obj)
            else:
                main(trading_bot_obj)
        except Exception as e:
            print(e)
            try:
                time.sleep(120)
            except Exception as e:
                print(e)
                time.sleep(5)
