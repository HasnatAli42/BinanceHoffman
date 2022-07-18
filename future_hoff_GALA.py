import os
import time
import requests
import numpy as np
import talib
import threading
import sqlite3 as sl
from numpy.core.defchararray import strip
from BinanceFuturesPy.futurespy import Client
from Counters import Counters
from Indicator import Indicator
from config import api_key, api_secret
from TradingBot import TradingBot
from settings import SYMBOL, QNTY, Leverage, Decimal_point_price, above_or_below_wick, client, \
    position_quantity_any_direction, TIME_PERIOD, LIMIT, position_info, position_quantity, TIME_SLEEP, \
    max_take_profit_limit

# When changing symbol change decimal points


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

con = sl.connect('orders-executed.db')
with con:
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS FUTURES_{SYMBOL}_HOFFMAN_TICKERS (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Order_sequence TEXT,
            Symbol TEXT,
            Order_type TEXT,
            Start_price TEXT,
            End_price TEXT,
            Operation_type TEXT,
            Total_Profit TEXT,
            Total_Loss TEXT,
            isValid TEXT,
            Time TEXT,
            Profit_Counter TEXT,
            Loss_Counter TEXT,
            Profit_First TEXT,
            Loss_First TEXT
        );
    """)

client.change_leverage(Leverage)


def take_profit_market():
    posInfo = position_info()
    entry_price = float(posInfo["entryPrice"])
    percent = (0.5 * entry_price) / 100
    return percent


def entry_price():
    posInfo = position_info()
    entry_price = float(posInfo["entryPrice"])
    return entry_price


def main(trade_bot_obj: TradingBot, counter_obj: Counters, indicator_obj: Indicator):
    while True:
        open, high, low, close = trade_bot_obj.get_data()
        indicator_obj.calculate(open_price=open,high=high,low=low,close=close)
        trade_bot_obj.currency_price = trade_bot_obj.get_price()

        if trade_bot_obj.Highest_Price < trade_bot_obj.currency_price:
            trade_bot_obj.Highest_Price = trade_bot_obj.currency_price
        if trade_bot_obj.LowestPrice > trade_bot_obj.currency_price:
            trade_bot_obj.LowestPrice = trade_bot_obj.currency_price

        if trade_bot_obj.firstRun:
            trade_bot_obj.firstRun = False
            indicator_obj.first_print(trade_bot_obj.currency_price)

        else:
            if trade_bot_obj.isOrderPlaced and trade_bot_obj.isLongOrderPlaced:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("\n************** Strategy Result Long Placed at: ",
                      trade_bot_obj.high_price + (trade_bot_obj.high_price * above_or_below_wick / 100), " ***********")
                print(f"Take Profit {trade_bot_obj.take_profit} |-------| Stop Loss {trade_bot_obj.stop_loss}")
                if not indicator_obj.long_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = True
                if indicator_obj.long_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.high_price = np.array(high)[-2]
                    trade_bot_obj.new_place_order_price = round(
                        trade_bot_obj.high_price + (trade_bot_obj.high_price * above_or_below_wick / 100),
                        Decimal_point_price)
                    if trade_bot_obj.new_place_order_price != trade_bot_obj.place_order_price:
                        client.cancel_all_open_orders(SYMBOL)
                        trade_bot_obj.place_order_price = trade_bot_obj.new_place_order_price
                        trade_bot_obj.place_long_order(long=trade_bot_obj.place_order_price)
                        trade_bot_obj.stop_loss = ((trade_bot_obj.place_order_price - indicator_obj.fast_primary_trend_line) / \
                                                   trade_bot_obj.place_order_price) * 100
                        trade_bot_obj.take_profit = trade_bot_obj.stop_loss * trade_bot_obj.profit_ratio
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
                    executed_order_on_wick_check = threading.Thread(target=trade_bot_obj.executed_order_on_wick_check, args=())
                    executed_order_on_wick_check.start()
                if indicator_obj.slow_speed_line < indicator_obj.fast_primary_trend_line or trade_bot_obj.take_profit > max_take_profit_limit:
                    print("Order Cancelled Successfully")
                    client.cancel_all_open_orders(SYMBOL)
                    trade_bot_obj.isOrderPlaced = False
                    trade_bot_obj.isLongOrderPlaced = False
                    trade_bot_obj.newHoffmanSignalCheck = False
                    if trade_bot_obj.take_profit > max_take_profit_limit:
                        trade_bot_obj.update_data_set("LongCancelledHigh")
                    else:
                        trade_bot_obj.update_data_set("LongCancelled")
                    trade_bot_obj.write_to_file()
                    trade_bot_obj.time_dot_round(TIME_PERIOD=TIME_PERIOD)
            elif trade_bot_obj.isOrderPlaced and trade_bot_obj.isShortOrderPlaced:
                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("\n************** Strategy Result Short Placed at: ", trade_bot_obj.place_order_price,
                      " ***********")
                print(f"Take Profit {trade_bot_obj.take_profit} |-------| Stop Loss {trade_bot_obj.stop_loss}")
                if not indicator_obj.short_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = True
                if indicator_obj.short_signal_candle:
                    trade_bot_obj.newHoffmanSignalCheck = False
                    trade_bot_obj.low_price = np.array(low)[-2]
                    trade_bot_obj.new_place_order_price = round(
                        trade_bot_obj.low_price - (trade_bot_obj.low_price * above_or_below_wick / 100),
                        Decimal_point_price)
                    if trade_bot_obj.new_place_order_price != trade_bot_obj.place_order_price:
                        client.cancel_all_open_orders(SYMBOL)
                        trade_bot_obj.place_order_price = trade_bot_obj.new_place_order_price
                        trade_bot_obj.place_short_order(short=trade_bot_obj.place_order_price)
                        trade_bot_obj.stop_loss = (indicator_obj.fast_primary_trend_line - trade_bot_obj.place_order_price) / \
                                                  trade_bot_obj.place_order_price * 100
                        trade_bot_obj.take_profit = trade_bot_obj.stop_loss * trade_bot_obj.profit_ratio
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
                    executed_order_on_wick_check = threading.Thread(target=trade_bot_obj.executed_order_on_wick_check,args=())
                    executed_order_on_wick_check.start()
                if indicator_obj.slow_speed_line > indicator_obj.fast_primary_trend_line or trade_bot_obj.take_profit > max_take_profit_limit:
                    print("Order Cancelled Successfully")
                    client.cancel_all_open_orders(SYMBOL)
                    trade_bot_obj.isOrderPlaced = False
                    trade_bot_obj.isShortOrderPlaced = False
                    trade_bot_obj.newHoffmanSignalCheck = False
                    if trade_bot_obj.take_profit > max_take_profit_limit:
                        trade_bot_obj.update_data_set("ShortCancelledHigh")
                    else:
                        trade_bot_obj.update_data_set("ShortCancelled")
                    trade_bot_obj.write_to_file()
                    trade_bot_obj.time_dot_round(TIME_PERIOD=TIME_PERIOD)
            elif trade_bot_obj.isOrderInProgress and trade_bot_obj.isLongOrderInProgress:

                if trade_bot_obj.currency_price < trade_bot_obj.place_order_price:
                    if counter_obj.isInProfit:
                        counter_obj.isInProfit = False
                        counter_obj.long_profit_counter_list.append(counter_obj.long_current_in_profit_counter)
                        if len(counter_obj.long_profit_counter_list) == 1 and len(counter_obj.long_loss_counter_list) == 0:
                            counter_obj.isProfitFirst = True
                        counter_obj.long_current_in_profit_counter = 0
                    counter_obj.long_current_in_loss_counter += 1
                    counter_obj.isInLoss = True
                    counter_obj.long_total_in_loss_counter += 1

                else:
                    if counter_obj.isInLoss:
                        counter_obj.isInLoss = False
                        counter_obj.long_loss_counter_list.append(counter_obj.long_current_in_loss_counter)
                        if len(counter_obj.long_profit_counter_list) == 0 and len(counter_obj.long_loss_counter_list) == 1:
                            counter_obj.isLossFirst = True
                        counter_obj.long_current_in_loss_counter = 0
                    counter_obj.long_current_in_profit_counter += 1
                    counter_obj.isInProfit = True
                    counter_obj.long_total_in_profit_counter += 1

                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("Take Profit:",
                      trade_bot_obj.place_order_price + (trade_bot_obj.place_order_price * trade_bot_obj.take_profit
                                                         / 100))
                print("Stop Loss:",
                      trade_bot_obj.place_order_price - (trade_bot_obj.place_order_price * trade_bot_obj.stop_loss /
                                                         100))
                print("\n************** Strategy Result Long In Progress ***********")
                counter_obj.long_print()
                trade_bot_obj.place_trailing_stop_loss()

                if counter_obj.is_order_in_profit_again(side="buy"):
                    trade_bot_obj.trailing_stop_loss_order(stop_loss_price= trade_bot_obj.place_order_price)
                    trade_bot_obj.isBreakEvenCalled = True

                if trade_bot_obj.isBreakEvenCalled:
                    if trade_bot_obj.currency_price > trade_bot_obj.place_order_price +(trade_bot_obj.place_order_price * 0.0015):
                        trade_bot_obj.trailing_stop_loss_order(stop_loss_price= trade_bot_obj.place_order_price +(trade_bot_obj.place_order_price * 0.001))
                        trade_bot_obj.isBreakEvenCalled = False

                if position_quantity() == 0:
                    client.cancel_all_open_orders(SYMBOL)
                    if trade_bot_obj.LongHit == "LongHit" and trade_bot_obj.currency_price > trade_bot_obj.place_order_price:
                        trade_bot_obj.LongHit = "LongHitProfit"
                    elif trade_bot_obj.LongHit == "LongHit" and trade_bot_obj.currency_price < trade_bot_obj.place_order_price:
                        trade_bot_obj.LongHit = "LongHitLoss"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isLongOrderInProgress = False
                    trade_bot_obj.isBreakEvenCalled = False
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.LongHit)
                    counter_obj.update_data_set_tickers(side="buy", SYMBOL=SYMBOL, LongHit=trade_bot_obj.LongHit,
                                                        ShortHit=trade_bot_obj.ShortHit,
                                                        order_sequence=trade_bot_obj.order_sequence,
                                                        place_order_price=trade_bot_obj.place_order_price,
                                                        currency_price=trade_bot_obj.currency_price)
                    counter_obj.long_clear()
                    trade_bot_obj.LongHit = "LongHit"
                    trade_bot_obj.write_to_file()
                if indicator_obj.slow_speed_line < indicator_obj.fast_primary_trend_line:
                    print("Order In-Progress Cancelled Successfully")
                    trade_bot_obj.LongHit = "LongHitCrossing"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isLongOrderInProgress = False
                    trade_bot_obj.isBreakEvenCalled = False
                    trade_bot_obj.cancel_executed_orders()
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.LongHit)
                    counter_obj.update_data_set_tickers(side="buy", SYMBOL=SYMBOL, LongHit=trade_bot_obj.LongHit,
                                                        ShortHit=trade_bot_obj.ShortHit,
                                                        order_sequence=trade_bot_obj.order_sequence,
                                                        place_order_price=trade_bot_obj.place_order_price,
                                                        currency_price=trade_bot_obj.currency_price)
                    counter_obj.long_clear()
                    trade_bot_obj.LongHit = "LongHit"
                    trade_bot_obj.write_to_file()
                if not trade_bot_obj.isOrderInProgress and not trade_bot_obj.isLongOrderInProgress:
                    print("Long Order Sleep Time is Called")
                    trade_bot_obj.update_data_set("sleep started")
                    trade_bot_obj.time_dot_round(TIME_PERIOD)
                    trade_bot_obj.update_data_set("sleep ended")
            elif trade_bot_obj.isOrderInProgress and trade_bot_obj.isShortOrderInProgress:

                if trade_bot_obj.currency_price > trade_bot_obj.place_order_price:
                    if counter_obj.isInProfit:
                        counter_obj.isInProfit = False
                        counter_obj.short_profit_counter_list.append(counter_obj.short_current_in_profit_counter)
                        if len(counter_obj.short_profit_counter_list) == 1 and len(counter_obj.short_loss_counter_list) == 0:
                            counter_obj.isProfitFirst = True

                        counter_obj.short_current_in_profit_counter = 0
                    counter_obj.short_current_in_loss_counter += 1
                    counter_obj.isInLoss = True
                    counter_obj.short_total_in_loss_counter += 1
                else:
                    if counter_obj.isInLoss:
                        counter_obj.isInLoss = False
                        counter_obj.short_loss_counter_list.append(counter_obj.short_current_in_loss_counter)
                        if len(counter_obj.short_profit_counter_list) == 0 and len(counter_obj.short_loss_counter_list) == 1:
                            counter_obj.isLossFirst = True

                        counter_obj.short_current_in_loss_counter = 0
                    counter_obj.short_current_in_profit_counter += 1
                    counter_obj.isInProfit = True
                    counter_obj.short_total_in_profit_counter += 1

                print("\n--------- Currency ---------")
                print(SYMBOL, ":", trade_bot_obj.currency_price)
                print("Take Profit:",
                      trade_bot_obj.place_order_price - (trade_bot_obj.place_order_price * trade_bot_obj.take_profit
                                                         / 100))
                print("Stop Loss:",
                      trade_bot_obj.place_order_price + (trade_bot_obj.place_order_price * trade_bot_obj.stop_loss /
                                                         100))
                print("\n************** Strategy Result Short In Progress ***********")
                counter_obj.short_print()
                trade_bot_obj.place_trailing_stop_loss()

                if counter_obj.is_order_in_profit_again(side="sell"):
                    trade_bot_obj.trailing_stop_loss_order(stop_loss_price= trade_bot_obj.place_order_price)
                    trade_bot_obj.isBreakEvenCalled = True

                if trade_bot_obj.isBreakEvenCalled:
                    if trade_bot_obj.currency_price < trade_bot_obj.place_order_price - (trade_bot_obj.place_order_price * 0.0015):
                        trade_bot_obj.trailing_stop_loss_order(stop_loss_price= trade_bot_obj.place_order_price -(trade_bot_obj.place_order_price * 0.001))
                        trade_bot_obj.isBreakEvenCalled = False

                if position_quantity() == 0:
                    client.cancel_all_open_orders(SYMBOL)
                    if trade_bot_obj.ShortHit == "ShortHit" and trade_bot_obj.currency_price < trade_bot_obj.place_order_price:
                        trade_bot_obj.ShortHit = "ShortHitProfit"
                    elif trade_bot_obj.ShortHit == "ShortHit" and trade_bot_obj.currency_price > trade_bot_obj.place_order_price:
                        trade_bot_obj.ShortHit = "ShortHitLoss"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isShortOrderInProgress = False
                    trade_bot_obj.isBreakEvenCalled = False
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.ShortHit)
                    counter_obj.update_data_set_tickers(side="sell", SYMBOL=SYMBOL, LongHit=trade_bot_obj.LongHit,
                                                        ShortHit=trade_bot_obj.ShortHit,
                                                        order_sequence=trade_bot_obj.order_sequence,
                                                        place_order_price=trade_bot_obj.place_order_price,
                                                        currency_price=trade_bot_obj.currency_price)
                    counter_obj.short_clear()
                    trade_bot_obj.ShortHit = "ShortHit"
                    trade_bot_obj.write_to_file()
                if indicator_obj.slow_speed_line > indicator_obj.fast_primary_trend_line:
                    print("Short Order In-Progress Cancelled Successfully")
                    trade_bot_obj.ShortHit = "ShortHitCrossing"
                    trade_bot_obj.isOrderInProgress = False
                    trade_bot_obj.isShortOrderInProgress = False
                    trade_bot_obj.isBreakEvenCalled = False
                    trade_bot_obj.cancel_executed_orders()
                    trade_bot_obj.order_sequence += 1
                    trade_bot_obj.update_data_set(trade_bot_obj.ShortHit)
                    counter_obj.update_data_set_tickers(side="sell", SYMBOL=SYMBOL, LongHit=trade_bot_obj.LongHit,
                                                        ShortHit=trade_bot_obj.ShortHit,
                                                        order_sequence=trade_bot_obj.order_sequence,
                                                        place_order_price=trade_bot_obj.place_order_price,
                                                        currency_price=trade_bot_obj.currency_price)
                    counter_obj.short_clear()
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
                print("\n************** Strategy Result Getting Order Number ", trade_bot_obj.order_sequence," ***********")
                if indicator_obj.slow_speed_line > indicator_obj.fast_primary_trend_line:
                    if indicator_obj.trend_line_1 >= indicator_obj.fast_primary_trend_line or indicator_obj.trend_line_2 >= indicator_obj.fast_primary_trend_line or indicator_obj.trend_line_3 >= indicator_obj.fast_primary_trend_line or indicator_obj.no_trend_zone_middle_line >= indicator_obj.fast_primary_trend_line:
                        print("Long Crossed But lines in between")
                    else:
                        print("Long Crossed looking for Hoffman Long signal wicked candle")
                        print("Hoffman Long Signal:", indicator_obj.long_signal_candle)
                        if indicator_obj.long_signal_candle:
                            trade_bot_obj.high_price = np.array(high)[-2]
                            trade_bot_obj.place_order_price = round(
                                trade_bot_obj.high_price + (trade_bot_obj.high_price * above_or_below_wick / 100),
                                Decimal_point_price)
                            trade_bot_obj.trailing_order_price = trade_bot_obj.place_order_price
                            trade_bot_obj.stop_loss = ((trade_bot_obj.place_order_price - indicator_obj.fast_primary_trend_line) / trade_bot_obj.place_order_price) * 100
                            trade_bot_obj.take_profit = trade_bot_obj.stop_loss * trade_bot_obj.profit_ratio
                            trade_bot_obj.isOrderPlaced = True
                            trade_bot_obj.isLongOrderPlaced = True
                            trade_bot_obj.place_long_order(long=trade_bot_obj.place_order_price)
                            trade_bot_obj.update_data_set("LongOrderPlaced")
                            trade_bot_obj.write_to_file()
                else:
                    if indicator_obj.trend_line_1 <= indicator_obj.fast_primary_trend_line or indicator_obj.trend_line_2 <= indicator_obj.fast_primary_trend_line or indicator_obj.trend_line_3 <= indicator_obj.fast_primary_trend_line or indicator_obj.no_trend_zone_middle_line <= indicator_obj.fast_primary_trend_line:
                        print("Short Crossed But lines in between")
                    else:
                        print("Short Crossed looking for Hoffman Short signal wicked candle")
                        print("Hoffman Short Signal:", indicator_obj.short_signal_candle)
                        if indicator_obj.short_signal_candle:
                            trade_bot_obj.low_price = np.array(low)[-2]
                            trade_bot_obj.place_order_price = round(
                                trade_bot_obj.low_price - (trade_bot_obj.low_price * above_or_below_wick / 100),
                                Decimal_point_price)
                            trade_bot_obj.trailing_order_price = trade_bot_obj.place_order_price
                            trade_bot_obj.stop_loss = (indicator_obj.fast_primary_trend_line - trade_bot_obj.place_order_price) / \
                                                      trade_bot_obj.place_order_price * 100
                            trade_bot_obj.take_profit = trade_bot_obj.stop_loss * trade_bot_obj.profit_ratio
                            trade_bot_obj.isOrderPlaced = True
                            trade_bot_obj.isShortOrderPlaced = True
                            trade_bot_obj.place_short_order(short=trade_bot_obj.place_order_price)
                            trade_bot_obj.update_data_set("ShortOrderPlaced")
                            trade_bot_obj.write_to_file()

        time.sleep(TIME_SLEEP)


if __name__ == "__main__":
    counters_obj = Counters()
    indicators_obj = Indicator()
    trading_bot_obj = TradingBot(api_key=api_key, secret_key=api_secret, stop_profit=0.5)
    while True:
        try:
            if os.path.exists(f'{SYMBOL}_is_order_in_progress.txt'):
                file = open(f'{SYMBOL}_is_order_in_progress.txt', 'r')
                x, y, z, xx, yy, zz, xxx, a, b, c, d, e, f, g = file.readlines()
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
                g = strip(g)
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
                trading_bot_obj.trailing_order_price = float(g)
                main(trading_bot_obj, counters_obj, indicators_obj)
            else:
                main(trading_bot_obj, counters_obj, indicators_obj)
        except Exception as e:
            print(e)
            try:
                time.sleep(20)
            except Exception as e:
                print(e)
                time.sleep(10)
