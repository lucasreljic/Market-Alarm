import requests, json, datetime
from trade import *
from datetime import datetime
from alpaca_trade_api.rest import REST, TimeFrame
from constants import APCA_API_KEY_ID, APCA_API_SECRET_KEY
datetime.now(tz=None)
ENDPOINT = "https://data.alpaca.markets/v2/iex/"

api = REST(key_id= APCA_API_KEY_ID, secret_key= APCA_API_SECRET_KEY,base_url= "https://data.alpaca.markets", raw_data= True)
datetimeobj = datetime.now()
timestampstr = datetimeobj.strftime("%Y-%b-%d (%H:%M:%S.%f)")
timestamppast = "2019-04-15T09:30:00-04:00"
HEADERS = {'APCA-API-KEY-ID': APCA_API_KEY_ID, 'APCA-API-SECRET-KEY': APCA_API_SECRET_KEY}


def getcryptoinfo(symbol):
    data = api.get_latest_crypto_quote(symbol, 'CBSE')
    return data

def getstockinfo(symbol):
    data = api.get_latest_quote(symbol)
    return data

def getcryptoprice(symbol):
    data = api.get_latest_crypto_quote(symbol, 'CBSE')
    j = data["ap"]
    return j

def getcryptobidprice(symbol):
    data = api.get_latest_crypto_quote(symbol, 'CBSE')
    j = data["bp"]
    return j

def getstockprice(symbol):
    data = api.get_latest_quote(symbol)
    j = data["ap"]
    return j

def getstockbidprice(symbol):
    data = api.get_latest_quote(symbol)
    j = data["bp"]
    return j

def getdfstock(symbol):
    data = api.get_latest_quote(symbol)
    spread = (data["ap"]) - data["bp"]
    return spread
