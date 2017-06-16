import json
import pprint
import requests
import hmac
import time
import hashlib
import api_key_config
import logging
import the_data
from fake_useragent import UserAgent

APIKEY = api_key_config.config['key']
APISECRET = api_key_config.config['secret']
PRIVATEAPIURL = 'https://c-cex.com/t/api.html'
PUBLICAPIURL = 'https://c-cex.com/t/api_pub.html'
TICKERSURL = 'https://c-cex.com/t/'

last_minute_price = None
# FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
handler = logging.FileHandler('/var/log/aib_trader.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('aibtrader')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def _build_private_api_request_url_string(params):
    s = PRIVATEAPIURL + '?'
    for k in params.keys():
        s += k + '=' + str(params[k]) + '&'
    return s[:-1]


def _build_tickers_request_url_string(content):
    return TICKERSURL + content


def _add_apikey_and_nonce(args):
    args['apikey'] = APIKEY
    args['nonce'] = int(time.time())
    return args


def _sign_request(url_str):
    m = hmac.new(APISECRET, url_str, hashlib.sha512)
    return m.hexdigest()


def _send_signed_request(url_str):
    ua = UserAgent()
    headers = {'apisign':_sign_request(url_str), 'User-Agent': ua.firefox}
    return requests.get(url_str, headers=headers)


def _send_unsigned_request(url_str):
    ua = UserAgent()
    headers = {'User-Agent': ua.firefox}
    return requests.get(url_str, headers=headers)


def _find_fastest_raising_current_of_last_minute(current_price):
    """
    Purpose
        compare the price of last minute and this minute to find out the fastest raising currency
        fastest raising could mean slowest dropping
    Precondition
        current_price is a dict
        last_minute_price is a global dict
    """
    largest_raise_percentage = -100000.0
    largest_raise_currency = ''
    for key in current_price.keys():
        if key.lower() is 'usd-btc':  # will not consider USD
            continue
        if not key.lower().endswith('-btc'):  # every currency is compared with BTC
            continue
        base = float(last_minute_price[key]['avg'])
        new_price = float(current_price[key]['avg'])
        try:
            raise_percentage = (new_price - base) / base
        except ZeroDivisionError:
            continue
        if raise_percentage > largest_raise_percentage:
            largest_raise_percentage = raise_percentage
            largest_raise_currency = key.replace('-btc', '')

    # todo: add log here
    return largest_raise_currency, largest_raise_percentage


def get_balance(currency_name):
    args = {'a': 'getbalance', 'currency': currency_name}
    args = _add_apikey_and_nonce(args)
    url_str = _build_private_api_request_url_string(args)
    return _send_signed_request(url_str).text


def get_balances():
    args = _add_apikey_and_nonce({'a': 'getbalances'})
    url_str = _build_private_api_request_url_string(args)
    return json.loads(_send_signed_request(url_str))


def get_prices():
    print _build_tickers_request_url_string('prices.json')
    resp = _send_unsigned_request(_build_tickers_request_url_string('prices.json'))
    if resp.status_code == '200':
        logger.debug('get prices succeed')
        return json.loads(resp.text)
    else:
        print resp.status_code
        logger.error('get prices failed with error code %s' % resp.status_code)
        return None


def purchase(spend_currency, target_currency, quantity=0, rate=0.00001):
    """
    :param spend_currency: coin to spend
    :param target_currency: coin to get
    :param quantity: how much target currency
    :param rate: constand according to api doc
    :return: the order uuid
    """
    market = spend_currency + '-' + target_currency
    if quantity == 0:  # means user wants to spend all spend_currency
        we_have = float(get_balance(spend_currency)['Available'])
        price = float(last_minute_price[market]['avg'])
        quantity = we_have / price
    params = {'market': market, 'quantity': quantity, 'rate': rate}
    resp = _send_signed_request(_build_private_api_request_url_string(params))
    if resp.status_code == '200':
        result = json.loads(resp.text)
        logger.debug(market + ',' + str(quantity) + ' order placed with ' + result['result'['uuid']])
        return result['result'['uuid']]
    else:
        logger.error(market + ',' + str(quantity) + ' order failed with %s' % resp.status_code)
        return None


if __name__ == '__main__':
    last_minute_price = the_data.last_minute_price
    # print _find_fastest_raising_current_of_last_minute(get_prices())
    print get_balance('AIB')
