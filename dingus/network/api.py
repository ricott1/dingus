import requests
from dingus.network.constants import ENDPOINTS


def fetch_block(block_id: bytes) -> dict:
    endpoint = ENDPOINTS["testnet"]
    url = f'{endpoint}/api/v2/blocks?blockId={block_id}'
    r = requests.get(url)
    return r.json()

def fetch_tx(tx_id: bytes) -> dict:
    endpoint = ENDPOINTS["testnet"]
    url = f'{endpoint}/api/transactions/{tx_id}'
    r = requests.get(url)
    return r.json()

def fetch_account(address: bytes) -> dict:
    endpoint = ENDPOINTS["testnet"]
    url = f'{endpoint}/api/v2/accounts?address={address}'
    r = requests.get(url)
    return r.json()

def fetch_account_from_public_key(public_key: bytes) -> dict:
    endpoint = ENDPOINTS["testnet"]
    url = f'{endpoint}/api/v2/accounts?publicKey={public_key}'
    r = requests.get(url)
    return r.json()

def send_tx(tx: str) -> dict:
    endpoint = ENDPOINTS["testnet"]
    url = f'{endpoint}/api/transactions'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    r = requests.post(url, data=tx, headers=headers)
    return r.json()