import requests

def fetch_block(block_id: bytes, protocol: str = "https", endpoint: str = "service.lisk.com", port: int = 443) -> dict:
    url = f'{protocol}://{endpoint}:{port}/api/v2/blocks?blockId={block_id}'
    r = requests.get(url)
    return r.json()

def fetch_tx(tx_id: bytes, protocol: str = "http", endpoint: str = "localhost", port: int = 4000) -> dict:
    url = f'{protocol}://{endpoint}:{port}/api/transactions/{tx_id}'
    r = requests.get(url)
    return r.json()

def fetch_account(address: bytes, protocol: str = "https", endpoint: str = "service.lisk.com", port: int = 443) -> dict:
    url = f'{protocol}://{endpoint}:{port}/api/v2/accounts?address={address}'
    r = requests.get(url)
    return r.json()

def fetch_account_from_public_key(public_key: bytes, protocol: str = "https", endpoint: str = "service.lisk.com", port: int = 443) -> dict:
    url = f'{protocol}://{endpoint}:{port}/api/v2/accounts?publicKey={public_key}'
    r = requests.get(url)
    return r.json()

def send_tx(tx: str, protocol: str = "https", endpoint: str = "service.lisk.com", port: int = 443) -> dict:
    url = f'{protocol}://{endpoint}:{port}/api/transactions'
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    r = requests.post(url, data=tx, headers=headers)
    return r.json()