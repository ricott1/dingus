from typing import Any
import requests
import os
from dingus.network.constants import ENDPOINTS, RPC_ENDPOINTS, RPC_REQUEST


def fetch_block(key: str, value: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/blocks?{key}={value}"
    r = requests.get(url)
    return r.json()


def fetch_tx(tx_id: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/transactions/{tx_id}"
    r = requests.get(url)
    return r.json()


def fetch_account(key: str, value: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/accounts?{key}={value}"
    r = requests.get(url)
    return r.json()


def send_transaction(hex_trs: str | bytes) -> None:
    if isinstance(hex_trs, bytes):
        hex_trs = hex_trs.hex()
    r = rpc_request(RPC_REQUEST.POST_TRANSACTION, {"transaction": f"{hex_trs}"}, "https://lisk.frittura.org")
    if r.status_code == 200:
        print("Send success:", r.json())
    else:
        print("Send failed", r)
    # net = os.environ["NETWORK"]
    # endpoint = ENDPOINTS[net]
    # url = f"{endpoint}/api/v2/transactions?transaction={hex_trs}"
    # headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    # r = requests.post(url, headers=headers)
    # return r.json()

def rpc_request(method: RPC_REQUEST | str, params: dict[str, str] = {}, endpoint: str = "") -> requests.Response:
    if isinstance(method, RPC_REQUEST):
        method = method.value
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": f"{method}"
    }
    if params:
        payload["params"] = params
    if not endpoint:
        net = os.environ["NETWORK"]
        endpoint = RPC_ENDPOINTS[net]
    url = f"{endpoint}/rpc"
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    print(f"Sending {payload} to {url}.")
    return requests.get(url, headers=headers, json=payload)


def network_status() -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/network/status"
    r = requests.get(url)
    return r.json()


def network_fees() -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/fees"
    r = requests.get(url)
    return r.json()


def market_prices() -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/market/prices"
    r = requests.get(url)
    return r.json()
