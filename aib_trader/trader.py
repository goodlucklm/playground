import requests
import hmac
import time
import hashlib
import api_key_config


def build_request_url_string(base, params):
    s = base + '?'
    for k in params.keys():
        s += k + '=' + str(params[k]) + '&'
    return s[:-1]


if __name__ == '__main__':
    api_base = 'https://c-cex.com/t/api.html'
    arguments = {'a': 'getbalance', 'currency': 'AIB', 'apikey': api_key_config.config['key'],
                 'nonce': int(time.time())}
    url_string = build_request_url_string(api_base, arguments)
    m = hmac.new(api_key_config.config['secret'], url_string, hashlib.sha512)
    signature = m.hexdigest()
    headers = {'apisign': signature}
    resp = requests.get(url_string, headers=headers)
    print resp.text
