import sqlite3 as sl
from datetime import datetime


class Counters:
    def __init__(self):
        self.short_total_in_loss_counter = 0
        self.long_total_in_loss_counter = 0
        self.short_current_in_loss_counter = 0
        self.long_current_in_loss_counter = 0
        self.short_loss_counter_list = []
        self.long_loss_counter_list = []
        self.short_total_in_profit_counter = 0
        self.long_total_in_profit_counter = 0
        self.short_current_in_profit_counter = 0
        self.long_current_in_profit_counter = 0
        self.short_profit_counter_list = []
        self.long_profit_counter_list = []
        self.isInProfit = False
        self.isInLoss = False
        self.isDataValid = False
        self.isProfitFirst = False
        self.isLossFirst = False


    def update_data_set_tickers(self, side, SYMBOL, LongHit, ShortHit, order_sequence, place_order_price,
                                currency_price):
        profit = []
        loss = []
        total_profit = 0
        total_loss = 0
        hit = ""
        if side == "buy":
            if self.isInProfit:
                self.long_profit_counter_list.append(self.long_current_in_profit_counter)
            elif self.isInLoss:
                self.long_loss_counter_list.append(self.long_current_in_loss_counter)
            profit = self.long_profit_counter_list
            loss = self.long_loss_counter_list
            total_profit = self.long_total_in_profit_counter
            total_loss = self.long_total_in_loss_counter
            if total_profit == sum(self.long_profit_counter_list) and total_loss == sum(self.long_loss_counter_list):
                self.isDataValid = True
            hit = LongHit

        elif side == "sell":
            if self.isInProfit:
                self.short_profit_counter_list.append(self.short_current_in_profit_counter)
            elif self.isInLoss:
                self.short_loss_counter_list.append(self.short_current_in_loss_counter)
            profit = self.short_profit_counter_list
            loss = self.short_loss_counter_list
            total_profit = self.short_total_in_profit_counter
            total_loss = self.short_total_in_loss_counter
            if total_profit == sum(self.short_profit_counter_list) and total_loss == sum(self.short_loss_counter_list):
                self.isDataValid = True
            hit = ShortHit
        con = sl.connect('orders-executed.db')
        sql = f'INSERT INTO FUTURES_{SYMBOL}_HOFFMAN_TICKERS (Order_sequence,  Symbol,' \
              'Order_type,' \
              'Start_price,End_price,Operation_type,Total_Profit,Total_Loss,isValid,Time,Profit_Counter,' \
              'Loss_Counter,Profit_First,Loss_First) values(?,?,?,?,?,?,?,' \
              '?,?,?,?,?,?,?) '

        data = [
            (str(order_sequence)), (str(SYMBOL)), (str(side)), (str(place_order_price)),
            (str(currency_price)), (str(hit)), (str(total_profit)), (str(total_loss)),
            (str(self.isDataValid)),
            (str(datetime.now())), (str(profit)), (str(loss)),(str(self.isProfitFirst)),(str(self.isLossFirst))
        ]
        with con:
            con.execute(sql, data)
            con.commit()

    def short_print(self):
        print("Current Short Loss   =", self.short_current_in_loss_counter)
        print("Total Short Loss     =", self.short_total_in_loss_counter)
        print("List  Short Loss     =", self.short_loss_counter_list)
        print("Current Short profit =", self.short_current_in_profit_counter)
        print("Total Short profit   =", self.short_total_in_profit_counter)
        print("List  Short profit   =", self.short_profit_counter_list)

    def long_print(self):
        print("Current Long Loss   =", self.long_current_in_loss_counter)
        print("Total Long Loss     =", self.long_total_in_loss_counter)
        print("List  Long Loss     =", self.long_loss_counter_list)
        print("Current Long profit =", self.long_current_in_profit_counter)
        print("Total Long profit   =", self.long_total_in_profit_counter)
        print("List  Long profit   =", self.long_profit_counter_list)

    def short_clear(self):
        self.short_current_in_loss_counter = 0
        self.short_total_in_loss_counter = 0
        self.short_loss_counter_list = []
        self.short_current_in_profit_counter = 0
        self.short_total_in_profit_counter = 0
        self.short_profit_counter_list = []
        self.isInProfit = False
        self.isInLoss = False
        self.isDataValid = False
        self.isLossFirst = False
        self.isProfitFirst = False

    def long_clear(self):
        self.long_current_in_loss_counter = 0
        self.long_total_in_loss_counter = 0
        self.long_loss_counter_list = []
        self.long_current_in_profit_counter = 0
        self.long_total_in_profit_counter = 0
        self.long_profit_counter_list = []
        self.isInProfit = False
        self.isInLoss = False
        self.isDataValid = False
        self.isLossFirst = False
        self.isProfitFirst = False

    def complete_clear(self):
        self.short_clear()
        self.long_clear()

    def is_order_in_profit_again(self, side):
        if side == "buy":
            if len(self.long_profit_counter_list) >= 1 and len(self.long_loss_counter_list) >= 1 and self.long_current_in_profit_counter > 3:
                return True
        elif side == "sell":
            if len(self.short_profit_counter_list) >= 1 and len(self.short_loss_counter_list) >= 1 and self.short_current_in_profit_counter > 3:
                return True
        return False



