from typing import Any
import requests
import os
from dingus.constants import Length
from dingus.network.constants import ENDPOINTS, RPC_ENDPOINTS, RPC_REQUEST
import json
from websocket import create_connection

def get_endpoint_from_chainID() -> str:
    if not "CHAIN_ID" in os.environ or os.environ["CHAIN_ID"].endswith("000000"):
        url = "https://lisk.frittura.org"
    else:
        url = "http://localhost:7887"
    return url

def node_request(method: RPC_REQUEST | str, params: dict[str, str] = {}, endpoint: str = "") -> dict[str, Any]:
    if not endpoint:
        endpoint = get_endpoint_from_chainID()
    if isinstance(method, RPC_REQUEST):
        method = method.value
    
    if "DEBUG" in os.environ and os.environ["DEBUG"] == "True":
        print(f"Sending {method}/{params} to {endpoint}.")
    if not "REQUEST_METHOD" in os.environ or os.environ["REQUEST_METHOD"] == "rpc":
        return rpc_request(method, params, endpoint).json()
    elif os.environ["REQUEST_METHOD"] == "socket":
        return json.loads(socket_request(method, params, endpoint))
    elif os.environ["REQUEST_METHOD"] == "service":
        return service_request(method, params, endpoint).json()

def service_request(method: str, params: dict[str, str], endpoint: str) -> requests.Response:
    url = f"{endpoint}/api/v2/{method}"
    if params:
        url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    return requests.post(url, headers=headers)

def rpc_request(method: str, params: dict[str, str], endpoint: str) -> requests.Response:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": f"{method}"
    }
    if params:
        payload["params"] = params
    url = f"{endpoint}/rpc"
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    return requests.get(url, headers=headers, json=payload)

def socket_request(method: str, params: dict[str, str], endpoint: str) -> Any | str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": f"{method}"
    }
    if params:
        payload["params"] = params
    url = f"{endpoint}/rpc-ws"
    ws = create_connection(url)
    ws.send(json.dumps(payload))
    result = ws.recv()
    ws.close()
    return result

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

# def network_status() -> dict:
#     net = os.environ["NETWORK"]
#     endpoint = ENDPOINTS[net]
#     url = f"{endpoint}/api/v2/network/status"
#     r = requests.get(url)
#     return r.json()


# def network_fees() -> dict:
#     net = os.environ["NETWORK"]
#     endpoint = ENDPOINTS[net]
#     url = f"{endpoint}/api/v2/fees"
#     r = requests.get(url)
#     return r.json()


# def market_prices() -> dict:
#     net = os.environ["NETWORK"]
#     endpoint = ENDPOINTS[net]
#     url = f"{endpoint}/api/v2/market/prices"
#     r = requests.get(url)
#     return r.json()


def get_node_info(endpoint: str = "") -> dict:
    return node_request("system_getNodeInfo", endpoint=endpoint)

def get_validator(address: str, endpoint: str = "") -> dict:
    return node_request("validators_getValidator", params={"address": f"{address}"}, endpoint=endpoint)

def get_generator_list(height: int, endpoint: str = "") -> dict:
    return node_request("chain_getGeneratorList", params={"height": height}, endpoint=endpoint)
    
def get_block_by_height(height: int, endpoint: str = "") -> dict:
    return node_request("chain_getBlockByHeight", params={"height": height}, endpoint=endpoint)

def get_events_by_height(height: int, endpoint: str = "") -> dict:
    return node_request("chain_getEvents", params={"height": height}, endpoint=endpoint)

def get_transaction_by_ID(id: str, endpoint: str = "") -> dict:
    return node_request("chain_getTransactionByID", params={"id": id}, endpoint=endpoint)

def get_bft_parameters_by_height(height: int, endpoint: str = "") -> dict:
    return node_request("consensus_getBFTParameters", params= {"height": height}, endpoint=endpoint)
        
def get_balance(address: str, endpoint: str = "") -> dict:
    return node_request(RPC_REQUEST.GET_BALANCE, params={"address": f"{address}"}, endpoint=endpoint)

def get_auth_account(address: str, endpoint: str = "") -> dict:
    return node_request("auth_getAuthAccount", params={"address": f"{address}"}, endpoint=endpoint)

def get_interop_account(endpoint: str = "") -> dict:
    return node_request("interoperability_getOwnChainAccount", endpoint=endpoint)

def get_chain_account(chainID: str, endpoint: str = "") -> dict:
    return node_request("interoperability_getChainAccount", params={"chainID": f"{chainID}"}, endpoint=endpoint)

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

def get_last_certificate(endpoint: str = "") -> dict:
    from dingus.types.block import Block
    from dingus.types.certificate import Certificate
    height = get_node_info(endpoint)["result"]["height"]
    block = Block.from_dict(get_block_by_height(height, endpoint)["result"])
    while len(block.header.aggregateCommit["certificateSignature"]) != Length.BLS_SIGNATURE:
        height -= 1
        print("Looking for signed certificate at height", height)
        # print(type(block.header.aggregateCommit["certificateSignature"]), len(block.header.aggregateCommit["certificateSignature"]))
        block = Block.from_dict(get_block_by_height(height, endpoint)["result"])
    return Certificate.from_block_header(block.header, endpoint = endpoint)

def send_transaction(hex_trs: str | bytes, endpoint: str = "") -> dict:
    if isinstance(hex_trs, bytes):
        hex_trs = hex_trs.hex()
    try:
        return node_request(RPC_REQUEST.POST_TRANSACTION, {"transaction": f"{hex_trs}"}, endpoint)
    except Exception as e:
        print(f"Error sending transaction: {e}")
        return {}