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

def get_endpoint_from_chainID() -> str:
    if os.environ["CHAIN_ID"].endswith("000000"):
        return "https://lisk.frittura.org"
    return "http://localhost:7887"


def send_transaction(hex_trs: str | bytes, endpoint: str = "") -> None:
    if isinstance(hex_trs, bytes):
        hex_trs = hex_trs.hex()
    
    if not endpoint:
        endpoint = get_endpoint_from_chainID()

    r = rpc_request(RPC_REQUEST.POST_TRANSACTION, {"transaction": f"{hex_trs}"}, endpoint)
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
        endpoint = get_endpoint_from_chainID()
    url = f"{endpoint}/rpc"
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    if "DEBUG" in os.environ and os.environ["DEBUG"] == "True":
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


def get_node_info(endpoint: str = "") -> dict:
    return rpc_request("system_getNodeInfo", endpoint=endpoint).json()

def get_validator(address: str, endpoint: str = "") -> dict:
    return rpc_request("validators_getValidator", params={"address": f"{address}"}, endpoint=endpoint).json()

def get_generator_list(height: int, endpoint: str = "") -> dict:
    return rpc_request("chain_getGeneratorList", params={"height": height}, endpoint=endpoint).json()
    
def get_block_by_height(height: int, endpoint: str = "") -> dict:
    return rpc_request("chain_getBlockByHeight", params={"height": height}, endpoint=endpoint).json()

def get_events_by_height(height: int, endpoint: str = "") -> dict:
    return rpc_request("chain_getEvents", params={"height": height}, endpoint=endpoint).json()

def get_transaction_by_ID(id: str, endpoint: str = "") -> dict:
    return rpc_request("chain_getTransactionByID", params={"id": id}, endpoint=endpoint).json()

def get_bft_parameters_by_height(height: int, endpoint: str = "") -> dict:
    return rpc_request("consensus_getBFTParameters", params= {"height": height}, endpoint=endpoint).json()
        
def get_balance(address: str, endpoint: str = "") -> dict:
    return rpc_request(RPC_REQUEST.GET_BALANCE, params={"address": f"{address}"}, endpoint=endpoint).json()

def get_auth_account(address: str, endpoint: str = "") -> dict:
    return rpc_request("auth_getAuthAccount", params={"address": f"{address}"}, endpoint=endpoint).json()

def get_interop_account(endpoint: str = "") -> dict:
    return rpc_request("interoperability_getOwnChainAccount", endpoint=endpoint).json()

def get_chain_account(chainID: str, endpoint: str = "") -> dict:
    return rpc_request("interoperability_getChainAccount", params={"chainID": f"{chainID}"}, endpoint=endpoint).json()

def get_last_bft_params(endpoint: str = "") -> tuple[list[dict[str, Any]], int]:
    if node_info := get_node_info(endpoint):
        finalized_height = node_info["result"]["finalizedHeight"]
    else:
        return ([], 0)

    bft_params = get_bft_parameters_by_height(finalized_height, endpoint)["result"]
    validators = [
        { 
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": v["bftWeight"],
            
        } for v in bft_params["validators"]]
    threshold = bft_params["certificateThreshold"]
    return (validators, threshold)

def get_last_finalized_block(endpoint: str = "") -> dict:
    if node_info := get_node_info(endpoint):
        finalized_height = node_info["result"]["finalizedHeight"]
    else:
        return {}
    return get_block_by_height(finalized_height, endpoint)["result"]