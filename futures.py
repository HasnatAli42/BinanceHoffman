import os
import time
from datetime import datetime
import requests
import talib
from BinanceFuturesPy.futurespy import Client
import sqlite3 as sl
import numpy
import websocket, json

con = sl.connect('orders-executed.db')
with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS FUTURES  (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Symbol TEXT,
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

symbol = "ETHUSDT"
api_key = "899c82ef4e40a434d16d7bce741ec03bc09cf202dcfa2c2780ad844273b40bb6"
api_secret = "b8c231a6c014841b95ff2e93cd5ba9f4713fe0963b7101081cbfc2e4b9fc66d9"
client = Client(api_key=api_key, sec_key=api_secret, testnet=True, symbol=symbol, recv_window=30000)

socket = "wss://stream.binance.com:9443/ws/ethbusd@kline_1m"
candle_close_list = []
position_type = False
position = False


def on_open(ws):
    print("connection_opened")


def on_close(ws):
    print("connection_close")


def on_message(ws, message):
    global position_type
    global position
    js_message = json.loads(message)
    candle = js_message['k']
    candle_close = candle['c']
    if candle['x'] == True:
        candle_close_list.append(candle_close)
        print(candle_close)
        print(candle_close_list)
        print(len(candle_close_list))
        print("Type of list = ", type(candle_close_list))
        if len(candle_close_list) > 7:
            print("Here")
            candle_np = numpy.array(candle_close_list)
            WMA4 = talib.EMA(candle_np, 4)
            WMA7 = talib.EMA(candle_np, 7)
            print(str(WMA4), str(WMA7))
            if is_cross(WMA7, WMA4):
                print("cross")
                if WMA7 > WMA4:
                    if position == True and position_type == True:
                        print("close_long_position")
                        order = client.new_order(symbol=symbol, orderType="MARKET", quantity=0.1, side="SELL",
                                                 reduceOnly=True)
                        client.cancel_all_open_orders(symbol)
                        position = False
                        pass
                    if not position:
                        print("short")
                        order = client.new_order(symbol=symbol, orderType="MARKET", quantity=0.1, side="SELL")
                        position_type = False
                        slp = stop_loss_price()
                        order_Sl = client.new_order(symbol=symbol, orderType="STOP_MARKET", quantity=0.1, side="BUY",
                                                    stopPrice=int(slp), reduceOnly=True)
                        print(order)
                        position = True
                if WMA4 > WMA7:
                    if position == True and position_type == False:
                        print("close_short_position")
                        order = client.new_order(symbol=symbol, orderType="MARKET", quantity=0.1, side="BUY",
                                                 reduceOnly=True)
                        client.cancel_all_open_orders(symbol)
                        position = False
                        pass
                    if not position:
                        print("long")
                        order = client.new_order(symbol=symbol, orderType="MARKET", quantity=0.1, side="BUY")
                        position_type = True
                        slp = stop_loss_price()
                        order_Sl = client.new_order(symbol=symbol, orderType="STOP_MARKET", quantity=0.1, side="SELL",
                                                    stopPrice=int(slp), reduceOnly=True)
                        print(order)
                        position = True


def position_info():
    posInfo = client.position_info()

    for counter in posInfo:
        if counter["symbol"] == symbol:
            print(counter)
            return counter


def stop_loss_price():
    posInfo = position_info()
    entry_price = float(posInfo["entryPrice"])
    percent = (0.3 * entry_price) / 100
    if position_type:
        return entry_price - percent
    if position_type == False:
        return entry_price + percent


def history():
    dt = datetime.now()
    dtold = datetime(dt.year, dt.month, dt.day - 6)
    millisecondold = int(round(dtold.timestamp() * 1000))
    millisecondnow = int(round(dt.timestamp() * 1000))
    his = client.trade_list(limit=1000, startTime=millisecondold, endTime=millisecondnow)
    print(his)


def balance():
    blnc = client.balance()
    print(blnc)


def take_profit_price():
    pass


def is_cross(WMA7, WMA4):
    if WMA7[-1] > WMA4 and WMA7[-2] < WMA4[-2]:
        print("short")
        return True

    if WMA7[-1] < WMA4 and WMA7[-2] > WMA4[-2]:
        print("long")
        return True

    else:
        print("not cross")
        return False


ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
