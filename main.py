import os
import time
from datetime import datetime
import requests
import numpy as np
import talib
from binance.client import Client  # importing client
import sqlite3 as sl

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

client = Client(api_key, api_secret)
# client.API_URL = 'https://testnet.binance.vision/api'
SYMBOL = "ETHBUSD"
TIME_PERIOD = "15m"
LIMIT = "1000"
QNTY = 0.22


class TradingBot:

    def __init__(self, api_key, secret_key, stop_profit):
        self.api_key = api_key
        self.secret_key = secret_key
        self.stop_profit = stop_profit
        self.remaining_quantity = QNTY
        self.client = Client(self.api_key, self.secret_key)
        # self.client.API_URL = 'https://testnet.binance.vision/api'
        self.buy = False
        self.sell = False
        self.currency_price = None
        self.quantity = QNTY / 5
        self.profit = None

    def buy_order(self):
        con = sl.connect('orders-executed.db')
        account_details = client.get_account()
        # 2 for BUSD 6 for USDT
        Usd_before_method_applied = account_details["balances"][188]["free"]
        Etherium_before_method_applied = account_details["balances"][2]["free"]
        Bnb_before_method_applied = account_details["balances"][4]["free"]
        order = self.client.create_order(symbol=SYMBOL, side="buy", quantity=QNTY, type="MARKET")
        account_details = client.get_account()
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

    def sell_order(self, qty):
        con = sl.connect('orders-executed.db')
        account_details = client.get_account()
        Usd_before_method_applied = account_details["balances"][188]["free"]
        Etherium_before_method_applied = account_details["balances"][2]["free"]
        Bnb_before_method_applied = account_details["balances"][4]["free"]
        order = self.client.create_order(symbol=SYMBOL, side="sell", quantity=qty, type="MARKET")
        account_details = client.get_account()
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

    def buy_strategy(self, ema_9, ema_26, last_ema_9, last_ema_26, rsi, buy):
        if ema_9 > ema_26 and last_ema_9:
            # if 2 > 1:
            if last_ema_9 < last_ema_26 and not buy:
                if rsi > 45 and rsi < 80:
                # if 2 > 1:
                    self.currency_price = self.get_price()
                    order = self.buy_order()
                    print(order['fills'])
                    buy_price = self.currency_price
                    self.profit = buy_price + ((buy_price * self.stop_profit) / 100)
                    file = open('stop_profit_loss.txt', 'w')
                    file.write(str(self.profit))
                    file.write("\n" + str(self.remaining_quantity))
                    file.write("\n" + str(self.quantity))
                    file.close()
                    file = open('rate.txt', 'a')
                    x, y = datetime.now().hour, datetime.now().minute
                    file.write(
                        f"\n{x}: {y} ===> {SYMBOL} Buy at: " + str(self.currency_price) + " -----> " + str(order)
                    )
                    file.close()
                    self.sell = True
                    self.buy = True

    def sell_strategy(self, ema_9, ema_26, last_ema_9, last_ema_26, rsi):
        self.currency_price = self.get_price()

        if self.currency_price >= self.profit:
            if self.remaining_quantity > 0:
                order = self.sell_order(self.quantity)
                print(order['fills'])
                x, y = datetime.now().hour, datetime.now().minute
                file = open('rate.txt', 'a')
                file.write(f"\n{x}: {y} ===> {SYMBOL} Gain Profit {self.profit}: " + str(
                    self.currency_price) + " -----> " + str(order))
                file.close()
                print(self.quantity, self.remaining_quantity)
                self.remaining_quantity = round((self.remaining_quantity - self.quantity), 4)
                self.profit *= 1.005
                print(self.profit)
                os.remove('stop_profit_loss.txt')
                file = open('stop_profit_loss.txt', 'w')
                file.write(str(self.profit))
                file.write("\n" + str(self.remaining_quantity))
                file.write("\n" + str(self.quantity))
                file.close()
            else:
                self.buy = False
                self.sell = False
                os.remove('stop_profit_loss.txt')
                time.sleep(20)
                return

        if ema_26 > ema_9 and last_ema_26:
            if last_ema_26 < last_ema_9:
                # if rsi < 45 and rsi > 20:
                if 2 > 1:
                    order = self.sell_order(self.remaining_quantity)
                    file = open('rate.txt', 'a')
                    x, y = datetime.now().hour, datetime.now().minute
                    file.write(
                        f"\n{x}: {y} ===> {SYMBOL} Cross Sale: " + str(self.currency_price) + " -----> " + str(order))
                    file.close()
                    self.buy = False
                    self.sell = False
                    os.remove('stop_profit_loss.txt')
                    time.sleep(20)
                    return


def main(trade_bot_obj: TradingBot):
    last_ema_9 = None
    last_ema_26 = None
    while True:
        closing_data = trade_bot_obj.get_data()
        trade_bot_obj.currency_price = trade_bot_obj.get_price()
        ema_9 = talib.EMA(closing_data, 9)[-1]
        ema_26 = talib.EMA(closing_data, 26)[-1]
        rsi = talib.RSI(closing_data, 14)[-1]

        print("\n--------- Currency ---------")
        print(SYMBOL, ":", trade_bot_obj.currency_price)
        print("----------------------------")
        print("\n************** Strategy Result ***********")
        print("EMA-9 Strategy : ", ema_9)
        print("EMA-26 Signal  : ", ema_26)
        print("RSI Strategy   : ", rsi)
        # print("Account Details : ",client.get_account())
        # trading_bot_obj.buy_order()
        # trading_bot_obj.sell_order(2)
        trade_bot_obj.buy_strategy(
            ema_9=ema_9,
            ema_26=ema_26,
            last_ema_9=last_ema_9,
            last_ema_26=last_ema_26,
            rsi=rsi,
            buy=trade_bot_obj.buy
        )
        while trade_bot_obj.sell:
            closing_data = trade_bot_obj.get_data()
            trade_bot_obj.currency_price = trade_bot_obj.get_price()
            ema_9 = talib.EMA(closing_data, 9)[-1]
            ema_26 = talib.EMA(closing_data, 26)[-1]
            rsi = talib.RSI(closing_data, 14)[-1]
            trade_bot_obj.sell_strategy(
                ema_9=ema_9,
                ema_26=ema_26,
                last_ema_9=last_ema_9,
                last_ema_26=last_ema_26,
                rsi=rsi
            )
            print("\n--------- Currency ---------")
            print(SYMBOL, ":", trade_bot_obj.currency_price)
            print("----------------------------")
            print("\n************** Sell Strategy Result ***********")
            print("EMA-9 Strategy : ", ema_9)
            print("EMA-26 Signal  : ", ema_26)
            print("RSI Strategy   : ", rsi)
            # print("Account Details : ", client.get_account())
            last_ema_9 = ema_9
            last_ema_26 = ema_26
            time.sleep(10)

        last_ema_9 = ema_9
        last_ema_26 = ema_26
        time.sleep(10)


if __name__ == "__main__":
    trading_bot_obj = TradingBot(api_key=api_key, secret_key=api_secret, stop_profit=0.5)
    while True:
        try:
            if os.path.exists("stop_profit_loss.txt"):
                file = open('stop_profit_loss.txt', 'r')
                x, z, q = file.readlines()
                file.close()
                trading_bot_obj.profit = float(x)
                trading_bot_obj.remaining_quantity = float(z)
                trading_bot_obj.quantity = float(q)
                trading_bot_obj.sell = True
                trading_bot_obj.buy = True
                main(trading_bot_obj)
            else:
                main(trading_bot_obj)
        except Exception as e:
            print(e)
            try:
                time.sleep(120)
            except Exception as e:
                print(e)
                time.sleep(10)
