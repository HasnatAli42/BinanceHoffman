import json
from types import SimpleNamespace
from django.db import models
from dataclasses import dataclass

data = '''{"makerCommission": 0, 
 "takerCommission": 0, 
 "buyerCommission": 0, 
 "sellerCommission": 0,
 "canTrade": true,
 "canWithdraw": false,
 "canDeposit": false,
 "updateTime": 1647856278814,
 "accountType": "SPOT",
 "balances": [{"asset": "BNB",  "free": 1000.00000000,   "locked": 0.00000000},
{"asset": "BTC",  "free": 1.00000000,      "locked": 0.00000000}, 
{"asset": "BUSD", "free": 10000.00000000,  "locked": 0.00000000},
{"asset": "ETH",  "free": 100.00000000,    "locked": 0.00000000}, 
{"asset": "LTC",  "free": 500.00000000,    "locked": 0.00000000}, 
{"asset": "TRX",  "free": 500000.00000000, "locked": 0.00000000},
{"asset": "USDT", "free": 10000.00000000,  "locked": 0.00000000},
{"asset": "XRP",  "free": 50000.00000000,  "locked": 0.00000000}],
 "permissions": ["SPOT"]
}'''

# Parse JSON into an object with attributes corresponding to dict keys.
x = json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
print(x.updateTime, x.balances[0], x.permissions)


# class GetAccountDetails(models.Model):
#     makerCommission = models.IntegerField
#     takerCommission = models.IntegerField
#     buyerCommission = models.IntegerField
#     sellerCommission = models.IntegerField
#     canTrade = models.BooleanField
#     canWithdraw = models.BooleanField
#     canDeposit = models.BooleanField
#     updateTime = models.IntegerField
#     accountType = models.TextField
#     permissions = models.TextField


class Balances(models.Model):
    asset = models.TextField
    free = models.FloatField
    locked = models.FloatField


@dataclass
class GetAccountDetails:
    makerCommission: int
    takerCommission: int
    buyerCommission: int
    sellerCommission: int
    canTrade: bool
    canWithdraw: bool
    canDeposit: bool
    updateTime: int
    canTrade: bool
    accountType: str
    permissions: str
    balances: list[Balances]


@dataclass
class Balances:
    asset: str
    free: float
    locked: float
