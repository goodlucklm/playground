#!/usr/bin/python

import time
import hmac
import hashlib
import base64
import requests

# https://novaexchange.com/remote/faq/

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

public_set = set(["markets", "market/info", "market/orderhistory", "market/openorders"])  # optional
private_set = set(
    ["getbalances", "getbalance", "getdeposits", "getwithdrawals", "getnewdepositaddress", "getdepositaddress",
     "myopenorders", "myopenorders_market", "cancelorder", "withdraw", "trade", "tradehistory", "getdeposithistory",
     "getwithdrawalhistory", "walletstatus"])


def api_query(method, req=None):
    my_url = "https://novaexchange.com/remote/v2/"
    if not req:
        req = {}
    if method.split('/')[0][0:6] == 'market':
        r = requests.get(my_url + method + '/', timeout=60)
    elif method.split('/')[0] in private_set:
        my_url += 'private/' + method + '/' + '?nonce=' + str(int(time.time()))
        req["apikey"] = API_KEY
        req["signature"] = base64.b64encode(hmac.new(API_SECRET, msg=my_url, digestmod=hashlib.sha512).digest())
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        r = requests.post(my_url, data=req, headers=headers, timeout=60)
    return r.text


# Eample usage:

# Public:
print api_query( "markets" )
# print api_query("market/orderhistory/" + "LTC_DOGE")
# etc...

# Private:
#print api_query("getbalances")
# print api_query( "trade/" + "LTC_DOGE", { 'tradebase': 0, 'tradetype': "BUY", 'tradeprice': 0.000001, 'tradeamount': 1000 } )
# print api_query( 'cancelorder/' + str( 1426936 ) )
# print api_query( 'tradehistory' )
# etc...
