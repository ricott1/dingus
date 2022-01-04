import requests
import os
from dingus.network.constants import ENDPOINTS


def fetch_block(key: str, value: str) -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/v2/blocks?{key}={value}'
    r = requests.get(url)
    return r.json()

def fetch_tx(tx_id: str) -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/transactions/{tx_id}'
    r = requests.get(url)
    return r.json()

def fetch_account(key: str, value: str) -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/v2/accounts?{key}={value}'
    r = requests.get(url)
    return r.json()

def send_tx(hex_trs: str) -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/v2/transactions?transaction={hex_trs}'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    r = requests.post(url, headers=headers)
    return r.json()

def network_status() -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/v2/network/status'
    r = requests.get(url)
    return r.json()

def network_fees() -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/v2/fees'
    r = requests.get(url)
    return r.json()

def market_prices() -> dict:
    net = os.environ["DINGUS_NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f'{endpoint}/api/v2/market/prices'
    r = requests.get(url)
    return r.json()