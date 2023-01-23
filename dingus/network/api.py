import requests
import os
from dingus.network.constants import ENDPOINTS, RPC_ENDPOINTS


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


def send_transaction(hex_trs: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = ENDPOINTS[net]
    url = f"{endpoint}/api/v2/transactions?transaction={hex_trs}"
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    r = requests.post(url, headers=headers)
    return r.json()

def rpc_post(method: str, params: dict[str, str]) -> dict:
    #"txpool_postTransaction"
    #{ "transaction": "0a036c6e731208726567697374657218002080cab5ee012a200c4862e7a9e80699b0d997a16336563fad3957bed28b09f7f8ed645827af0f9c320e0a07626c612e6c736b10d83618023a40006ab73f5ed3dd0f5008575525154f22226cec78d86b57ddd0b83af7a7d386ea6db581afd7f536e325a231bcf910d622253b3c3b5bd89f6df5f46eb51285af05" }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": {method}
    }
    payload["params"] = params
    net = os.environ["NETWORK"]
    endpoint = RPC_ENDPOINTS[net]
    url = f"{endpoint}/rpc"
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    r = requests.post(url, headers=headers, data=payload)
    return r.json()

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
