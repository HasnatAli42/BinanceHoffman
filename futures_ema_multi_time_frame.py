import os
import time
from datetime import datetime
import requests
import numpy as np
import talib
from binance.client import Client as Client1  # importing client
import sqlite3 as sl

from numpy.core.defchararray import strip

from BinanceFuturesPy.futurespy import Client

from config import api_key, api_secret

con = sl.connect('orders-executed.db')
with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS ETHBUSD  (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Current_eth_price TEXT,
            Current_ema_higher TEXT,
            Current_ema_lower TEXT,
            Etherium_quantity TEXT,
            Usd_before_method_applied TEXT,
            Usd_after_method_applied TEXT,
            Etherium_before_method_applied TEXT,
            Etherium_after_method_applied TEXT,
            Bnb_before_method_applied TEXT,
            Bnb_after_method_applied TEXT,
            Method_applied TEXT,
            Usd_used TEXT,
            Time TEXT
        );
    """)

client1 = Client1(api_key, api_secret)
# client.API_URL = 'https://testnet.binance.vision/api'
SYMBOL = "ETHUSDT"
TIME_PERIOD = "15m"
LIMIT = "210"
QNTY = 0.02
client = Client(api_key=api_key, sec_key=api_secret, testnet=False, symbol=SYMBOL, recv_window=30000)


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
    percent = (0.5 * entry_price) / 100
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
        self.remaining_quantity = QNTY
        self.client = Client(api_key=api_key, sec_key=secret_key, testnet=False, symbol=SYMBOL, recv_window=30000)
        # self.client.API_URL = 'https://testnet.binance.vision/api'
        self.isOrderInProgress = False
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = False
        self.currency_price = None
        self.quantity = QNTY / 5
        self.profit = None
        self.firstRun = True

    def buy_order_without_any_in_progress(self):
        con = sl.connect('orders-executed.db')
        account_details = client1.get_account()
        # 2 for BUSD 6 for USDT
        Usd_before_method_applied = account_details["balances"][188]["free"]
        Etherium_before_method_applied = account_details["balances"][2]["free"]
        Bnb_before_method_applied = account_details["balances"][4]["free"]
        client.cancel_all_open_orders(SYMBOL)
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = True
        self.isShortOrderInProgress = False
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((1 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((2 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((3 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((4 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((5 * take_profit) + order_entry_price), reduceOnly=True)
        account_details = client1.get_account()
        Usd_after_method_applied = account_details["balances"][188]["free"]
        Etherium_after_method_applied = account_details["balances"][2]["free"]
        Bnb_before_after_applied = account_details["balances"][4]["free"]
        sql = 'INSERT INTO ETHBUSD (Current_eth_price, Current_ema_higher, Current_ema_lower,Etherium_quantity,' \
              'Usd_before_method_applied,Usd_after_method_applied,Etherium_before_method_applied,' \
              'Etherium_after_method_applied,Bnb_before_method_applied,Bnb_after_method_applied,Method_applied,' \
              'Usd_used,Time) values(?,?,?,?,?,?,?,?,?,?,?,?,?) '
        data = [
            (str(self.currency_price)), ("9"), ("26"), (str(QNTY)), (str(Usd_before_method_applied)),
            (str(Usd_after_method_applied)),
            (str(Etherium_before_method_applied)), (str(Etherium_after_method_applied)),
            (str(Bnb_before_method_applied)), (str(Bnb_before_after_applied)), ("buy"),
            (str(self.currency_price * QNTY)), (str(datetime.now())),
        ]
        with con:
            con.execute(sql, data)
            con.commit()
            # con.close()

        return order

    def buy_order(self):
        con = sl.connect('orders-executed.db')
        account_details = client1.get_account()
        # 2 for BUSD 6 for USDT
        Usd_before_method_applied = account_details["balances"][188]["free"]
        Etherium_before_method_applied = account_details["balances"][2]["free"]
        Bnb_before_method_applied = account_details["balances"][4]["free"]
        client.cancel_all_open_orders(SYMBOL)
        quantity = position_quantity()
        if quantity > 0:
            order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=quantity, side="BUY")
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="BUY")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = True
        self.isShortOrderInProgress = False
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((1 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((2 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((3 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((4 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="SELL",
                                    stopPrice=int((5 * take_profit) + order_entry_price), reduceOnly=True)
        account_details = client1.get_account()
        Usd_after_method_applied = account_details["balances"][188]["free"]
        Etherium_after_method_applied = account_details["balances"][2]["free"]
        Bnb_before_after_applied = account_details["balances"][4]["free"]
        sql = 'INSERT INTO ETHBUSD (Current_eth_price, Current_ema_higher, Current_ema_lower,Etherium_quantity,' \
              'Usd_before_method_applied,Usd_after_method_applied,Etherium_before_method_applied,' \
              'Etherium_after_method_applied,Bnb_before_method_applied,Bnb_after_method_applied,Method_applied,' \
              'Usd_used,Time) values(?,?,?,?,?,?,?,?,?,?,?,?,?) '
        data = [
            (str(self.currency_price)), ("9"), ("26"), (str(QNTY)), (str(Usd_before_method_applied)),
            (str(Usd_after_method_applied)),
            (str(Etherium_before_method_applied)), (str(Etherium_after_method_applied)),
            (str(Bnb_before_method_applied)), (str(Bnb_before_after_applied)), ("buy"),
            (str(self.currency_price * QNTY)), (str(datetime.now())),
        ]
        with con:
            con.execute(sql, data)
            con.commit()
            # con.close()

        return order

    def sell_order_without_any_in_progress(self, qty):
        con = sl.connect('orders-executed.db')
        account_details = client1.get_account()
        Usd_before_method_applied = account_details["balances"][188]["free"]
        Etherium_before_method_applied = account_details["balances"][2]["free"]
        Bnb_before_method_applied = account_details["balances"][4]["free"]
        client.cancel_all_open_orders(SYMBOL)
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = True
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(1 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(2 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(3 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(4 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(5 * take_profit) + order_entry_price), reduceOnly=True)
        account_details = client1.get_account()
        Usd_after_method_applied = account_details["balances"][188]["free"]
        Etherium_after_method_applied = account_details["balances"][2]["free"]
        Bnb_before_after_applied = account_details["balances"][4]["free"]
        sql = 'INSERT INTO ETHBUSD (Current_eth_price, Current_ema_higher, Current_ema_lower,Etherium_quantity,' \
              'Usd_before_method_applied,Usd_after_method_applied,Etherium_before_method_applied,' \
              'Etherium_after_method_applied,Bnb_before_method_applied,Bnb_after_method_applied,Method_applied,' \
              'Usd_used,Time) values(?,?,?,?,?,?,?,?,?,?,?,?,?) '
        data = [
            (str(self.currency_price)), ("9"), ("26"), (str(QNTY)), (str(Usd_before_method_applied)),
            (str(Usd_after_method_applied)),
            (str(Etherium_before_method_applied)), (str(Etherium_after_method_applied)),
            (str(Bnb_before_method_applied)), (str(Bnb_before_after_applied)), ("sell"),
            (str(self.currency_price * qty)), (str(datetime.now())),
        ]
        with con:
            con.execute(sql, data)
            con.commit()

        return order

    def sell_order(self, qty):
        con = sl.connect('orders-executed.db')
        account_details = client1.get_account()
        Usd_before_method_applied = account_details["balances"][188]["free"]
        Etherium_before_method_applied = account_details["balances"][2]["free"]
        Bnb_before_method_applied = account_details["balances"][4]["free"]
        client.cancel_all_open_orders(SYMBOL)
        quantity = position_quantity()
        if quantity > 0:
            order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=quantity, side="SELL")
        order = client.new_order(symbol=SYMBOL, orderType="MARKET", quantity=QNTY, side="SELL")
        self.isOrderInProgress = True
        self.isLongOrderInProgress = False
        self.isShortOrderInProgress = True
        file = open('is_order_in_progress.txt', 'w')
        file.write(str(self.isOrderInProgress))
        file.write("\n" + str(self.isLongOrderInProgress))
        file.write("\n" + str(self.isShortOrderInProgress))
        file.close()
        take_profit = take_profit_market()
        order_entry_price = entry_price()
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(1 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(2 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(3 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(4 * take_profit) + order_entry_price), reduceOnly=True)
        order_Sl = client.new_order(symbol=SYMBOL, orderType="TAKE_PROFIT_MARKET", quantity=QNTY / 5, side="BUY",
                                    stopPrice=int(-(5 * take_profit) + order_entry_price), reduceOnly=True)
        account_details = client1.get_account()
        Usd_after_method_applied = account_details["balances"][188]["free"]
        Etherium_after_method_applied = account_details["balances"][2]["free"]
        Bnb_before_after_applied = account_details["balances"][4]["free"]
        sql = 'INSERT INTO ETHBUSD (Current_eth_price, Current_ema_higher, Current_ema_lower,Etherium_quantity,' \
              'Usd_before_method_applied,Usd_after_method_applied,Etherium_before_method_applied,' \
              'Etherium_after_method_applied,Bnb_before_method_applied,Bnb_after_method_applied,Method_applied,' \
              'Usd_used,Time) values(?,?,?,?,?,?,?,?,?,?,?,?,?) '
        data = [
            (str(self.currency_price)), str("9"), str("26"), (str(QNTY)), (str(Usd_before_method_applied)),
            (str(Usd_after_method_applied)),
            (str(Etherium_before_method_applied)), (str(Etherium_after_method_applied)),
            (str(Bnb_before_method_applied)), (str(Bnb_before_after_applied)), str("sell"),
            (str(self.currency_price * qty)), (str(datetime.now())),
        ]
        with con:
            con.execute(sql, data)
            con.commit()

        return order

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

    def get_data_30_from_15(self, closing_data_15: np.array):
        determiner = datetime.now().minute
        closing_data_30 = closing_data_15
        print("Time =", determiner)
        if determiner < 15 or 30 < determiner < 45:
            i = -3
            while i > -100:
                closing_data_30 = np.delete(closing_data_30, i)
                i = i - 1
        else:
            i = -2
            while i > -100:
                closing_data_30 = np.delete(closing_data_30, i)
                i = i - 1
        return closing_data_30


trading_bot_obj = TradingBot(api_key=api_key, secret_key=api_secret, stop_profit=0.5)
closing_data = trading_bot_obj.get_data()
closing_data_30 = trading_bot_obj.get_data_30_from_15(closing_data)
print("15min = ", closing_data, "Length = ", len(closing_data))
print("30min = ", closing_data_30, "Length = ", len(closing_data_30))
# def main(trade_bot_obj: TradingBot):
#     last_ema_9 = None
#     last_ema_26 = None
#     while True:
#         closing_data = trade_bot_obj.get_data()
#         trade_bot_obj.currency_price = trade_bot_obj.get_price()
#         ema_9 = talib.EMA(closing_data, 9)[-1]
#         ema_26 = talib.EMA(closing_data, 26)[-1]
#         rsi = talib.RSI(closing_data, 14)[-1]
#         # trade_bot_obj.buy_order_without_any_in_progress()
#         # trade_bot_obj.sell_order(QNTY)
#         # trade_bot_obj.buy_order()
#         # trade_bot_obj.sell_order_without_any_in_progress(QNTY)
#         if trade_bot_obj.firstRun:
#             trade_bot_obj.firstRun = False
#             print("\n--------- Currency ---------")
#             print(SYMBOL, ":", trade_bot_obj.currency_price)
#             print("----------------------------")
#             print("\n************** Strategy Result First Run ***********")
#             print("EMA-9 Strategy : ", ema_9)
#             print("EMA-26 Signal  : ", ema_26)
#             print("RSI Strategy   : ", rsi)
#         else:
#             if trade_bot_obj.isOrderInProgress and trade_bot_obj.isLongOrderInProgress:
#                 print("\n--------- Currency ---------")
#                 print(SYMBOL, ":", trade_bot_obj.currency_price)
#                 print("----------------------------")
#                 print("\n************** Strategy Result Long In Progress ***********")
#                 print("EMA-9 Strategy : ", ema_9)
#                 print("EMA-26 Signal  : ", ema_26)
#                 print("RSI Strategy   : ", rsi)
#                 if ema_26 > ema_9 and last_ema_26:
#                     if last_ema_26 < last_ema_9:
#                         trade_bot_obj.sell_order(QNTY)
#             elif trade_bot_obj.isOrderInProgress and trade_bot_obj.isShortOrderInProgress:
#                 print("\n--------- Currency ---------")
#                 print(SYMBOL, ":", trade_bot_obj.currency_price)
#                 print("----------------------------")
#                 print("\n************** Strategy Result Short In Progress ***********")
#                 print("EMA-9 Strategy : ", ema_9)
#                 print("EMA-26 Signal  : ", ema_26)
#                 print("RSI Strategy   : ", rsi)
#                 if ema_9 > ema_26 and last_ema_9:
#                     if last_ema_9 < last_ema_26:
#                         trade_bot_obj.buy_order()
#             elif not trade_bot_obj.isOrderInProgress:
#                 print("\n--------- Currency ---------")
#                 print(SYMBOL, ":", trade_bot_obj.currency_price)
#                 print("----------------------------")
#                 print("\n************** Strategy Result Getting First Order ***********")
#                 print("EMA-9 Strategy : ", ema_9)
#                 print("EMA-26 Signal  : ", ema_26)
#                 print("RSI Strategy   : ", rsi)
#                 if ema_26 > ema_9 and last_ema_26:
#                     if last_ema_26 < last_ema_9:
#                         trade_bot_obj.sell_order_without_any_in_progress(QNTY)
#                 if ema_9 > ema_26 and last_ema_9:
#                     if last_ema_9 < last_ema_26:
#                         trade_bot_obj.buy_order_without_any_in_progress()
#         last_ema_9 = ema_9
#         last_ema_26 = ema_26
#         time.sleep(10)
#
#
# if __name__ == "__main__":
#     trading_bot_obj = TradingBot(api_key=api_key, secret_key=api_secret, stop_profit=0.5)
#     while True:
#         try:
#             if os.path.exists("is_order_in_progress.txt"):
#                 file = open('is_order_in_progress.txt', 'r')
#                 x, y, z = file.readlines()
#                 file.close()
#                 x = strip(x)
#                 y = strip(y)
#                 z = strip(z)
#                 if x == "True":
#                     trading_bot_obj.isOrderInProgress = True
#                 if y == "True":
#                     trading_bot_obj.isLongOrderInProgress = True
#                 if z == "True":
#                     trading_bot_obj.isShortOrderInProgress = True
#                 main(trading_bot_obj)
#             else:
#                 main(trading_bot_obj)
#         except Exception as e:
#             print(e)
#             try:
#                 time.sleep(120)
#             except Exception as e:
#                 print(e)
#                 time.sleep(10)
