import requests
from BinanceFuturesPy.futurespy import Client
from config import api_key, api_secret

SYMBOL = "GALABUSD"
Decimal_point_price = 6
Decimal_point_qty = 0
Dollar = 15
Leverage = 1
TIME_PERIOD = "3m"
LIMIT = "300"
TIME_SLEEP = 2
Dollars = Dollar * Leverage
above_or_below_wick = 0.1
trailing_order_check = 0.5
trailing_order_increase = 0.5
max_take_profit_limit = 1.5
client = Client(api_key=api_key, sec_key=api_secret, testnet=False, symbol=SYMBOL, recv_window=30000)


def dollars_to_cryto_quantiy(quantity):
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
    except Exception as e:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={SYMBOL}"
    res = requests.get(url)
    return round((quantity / float(res.json()['price'])), Decimal_point_qty)


QNTY = dollars_to_cryto_quantiy(Dollars)


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
