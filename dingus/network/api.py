from __future__ import annotations
from typing import Any, TYPE_CHECKING
import requests
import os
from dingus.network.constants import RPC_ENDPOINTS, RPC_REQUEST, SOCKET_ENDPOINTS, SERVICE_ENDPOINTS
import json
from websocket import create_connection
if TYPE_CHECKING:
    from dingus.types.block import Block
    from dingus.types.certificate import Certificate



def get_endpoint_from_chainID() -> str:
    if not "CHAIN_ID" in os.environ or os.environ["CHAIN_ID"].endswith("000000"):
        url = "206.189.5.168:4002"
    else:
        url = "localhost:7887"
    return url

def node_request(method: RPC_REQUEST | str, params: dict[str, str] = {}, endpoint: str = "") -> dict:
    if isinstance(method, RPC_REQUEST):
        method = method.value

    if not "REQUEST_METHOD" in os.environ or os.environ["REQUEST_METHOD"] == "rpc":
        resp = rpc_request(method, params, endpoint)
    elif os.environ["REQUEST_METHOD"] == "socket":
        resp = socket_request(method, params, endpoint)
        return json.loads(resp)
    elif os.environ["REQUEST_METHOD"] == "service":
        resp = service_request(method, params, endpoint)
    if resp.status_code != 200:
        raise Exception(f"Error: {resp.text}")
    return resp.json()

def service_request(method: str, params: dict[str, str], endpoint: str = "") -> requests.Response:
    if not endpoint:
        endpoint = SERVICE_ENDPOINTS[os.environ["NETWORK"]]
    if params:
        endpoint += f"{method}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    return requests.post(endpoint, headers=headers)

def rpc_request(method: str, params: dict[str, str], endpoint: str = "") -> requests.Response:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": f"{method}"
    }
    if params:
        payload["params"] = params
    if not endpoint:
        endpoint = RPC_ENDPOINTS[os.environ["NETWORK"]]
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    # print(f"RPC: Sending {method}/{params} to {endpoint}.")
    return requests.post(f"http://{endpoint}/rpc", headers=headers, json=payload)

def socket_request(method: str, params: dict[str, str], endpoint: str = "") -> Any | str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": f"{method}"
    }
    if params:
        payload["params"] = params
    if not endpoint:
        endpoint = SOCKET_ENDPOINTS[os.environ["NETWORK"]]
    ws = create_connection(f"ws://{endpoint}/rpc-ws")
    ws.send(json.dumps(payload))
    result = ws.recv()
    ws.close()
    return result

def fetch_block(key: str, value: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = SERVICE_ENDPOINTS[net]
    url = f"{endpoint}/api/v2/blocks?{key}={value}"
    r = requests.get(url)
    return r.json()


def fetch_tx(tx_id: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = SERVICE_ENDPOINTS[net]
    url = f"{endpoint}/api/v2/transactions/{tx_id}"
    r = requests.get(url)
    return r.json()


def fetch_account(key: str, value: str) -> dict:
    net = os.environ["NETWORK"]
    endpoint = SERVICE_ENDPOINTS[net]
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


def kraken_market_price() -> float:
    r = requests.get('https://api.kraken.com/0/public/Trades?pair=LSKUSD')
    return r.json()["result"]["LSKUSD"][-1][0]

def get_node_info(endpoint: str = "") -> dict:
    return node_request("system_getNodeInfo", endpoint=endpoint)

def get_pos_validator(address: str, endpoint: str = "") -> dict:
    return node_request("pos_getValidator", params={"address": f"{address}"}, endpoint=endpoint)

def get_all_pos_validator(endpoint: str = "") -> dict:
    return node_request("pos_getAllValidators", endpoint=endpoint)

def get_generator_keys(endpoint: str = "") -> dict:
    return node_request("generator_getAllKeys", endpoint=endpoint)

def get_min_fee_per_byte(endpoint: str = "") -> dict:
    return node_request("fee_getMinFeePerByte", endpoint=endpoint)

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

def get_escrowed_amounts(endpoint: str = "") -> dict:
    return node_request("token_getEscrowedAmounts", endpoint=endpoint)

def get_auth_account(address: str, endpoint: str = "") -> dict:
    return node_request("auth_getAuthAccount", params={"address": f"{address}"}, endpoint=endpoint)

def get_own_chain_account(endpoint: str = "") -> dict:
    return node_request("interoperability_getOwnChainAccount", endpoint=endpoint)

def get_chain_account(chainID: str, endpoint: str = "") -> dict:
    return node_request("interoperability_getChainAccount", params={"chainID": f"{chainID}"}, endpoint=endpoint)

def get_channel(chainID: str, endpoint: str = "") -> dict:
    return node_request("interoperability_getChannel", params={"chainID": f"{chainID}"}, endpoint=endpoint)

def get_chain_validators(chainID: str, endpoint: str = "") -> dict:
    return node_request("interoperability_getChainValidators", params={"chainID": f"{chainID}"}, endpoint=endpoint)

def get_last_bft_params(endpoint: str = "") -> dict:
    height = get_node_info(endpoint)["result"]["height"]
    return get_bft_parameters_by_height(height, endpoint)

def get_last_finalized_bft_params(endpoint: str = "") -> dict:
    finalized_height = get_node_info(endpoint)["result"]["finalizedHeight"]
    return get_bft_parameters_by_height(finalized_height, endpoint)

def get_last_finalized_block(endpoint: str = "") -> dict:
    if node_info := get_node_info(endpoint):
        finalized_height = node_info["result"]["finalizedHeight"]
    else:
        return {}
    return get_block_by_height(finalized_height, endpoint)["result"]

def get_last_block(endpoint: str = "") -> Block:
    if node_info := get_node_info(endpoint):
        height = node_info["result"]["height"]
    else:
        return {}
    from dingus.types.block import Block
    return Block.from_dict(get_block_by_height(height, endpoint)["result"])


def get_last_certificate(endpoint: str = "") -> Certificate:
    from dingus.types.block import Block
    from dingus.types.certificate import Certificate
    height = get_node_info(endpoint)["result"]["height"]
    chainID = bytes.fromhex(get_node_info(endpoint)["result"]["chainID"])
    block = Block.from_dict(get_block_by_height(height, endpoint)["result"])
    while True:
        certificate = Certificate.from_block_header(block.header, endpoint = endpoint)
        bft_parameters = get_bft_parameters_by_height(certificate.height, endpoint)["result"]
        validators = [{"blsKey": bytes.fromhex(validator["blsKey"]), "bftWeight": int(validator["bftWeight"])} for validator in bft_parameters["validators"]]
        print("Verifying certificate at height", certificate.height)

        if certificate.verify_signature(validators, int(bft_parameters["certificateThreshold"]), chainID):
            break
        
        height -= 1
        print("Looking for signed certificate at height", height)
        block = Block.from_dict(get_block_by_height(height, endpoint)["result"])
    return certificate

def get_last_valid_certificate(from_endpoint: str, target_endpoint: str) -> Certificate:
    from dingus.types.block import Block
    from dingus.types.certificate import Certificate
    height = get_node_info(from_endpoint)["result"]["height"]
    chainID = get_node_info(from_endpoint)["result"]["chainID"]
    last_certified_validators_data = get_chain_validators(chainID, target_endpoint)["result"]
    print(last_certified_validators_data)

    last_certified_validators = [{"blsKey": bytes.fromhex(validator["blsKey"]), "bftWeight": int(validator["bftWeight"])} for validator in last_certified_validators_data["activeValidators"]]
    last_certified_certificate_threshold = int(last_certified_validators_data["certificateThreshold"])
    block = Block.from_dict(get_block_by_height(height, from_endpoint)["result"])
    while True:
        certificate = Certificate.from_block_header(block.header, endpoint = from_endpoint)
        # bft_parameters = get_bft_parameters_by_height(certificate.height, from_endpoint)["result"]
        # validators = [{"blsKey": bytes.fromhex(validator["blsKey"]), "bftWeight": int(validator["bftWeight"])} for validator in bft_parameters["validators"]]
        if certificate.height == 0:
            continue
        print("Verifying certificate at height", certificate.height)

        if certificate.verify_signature(last_certified_validators, last_certified_certificate_threshold, bytes.fromhex(chainID)):
            break
        
        height -= 1
        print("Looking for signed certificate at height", height)
        block = Block.from_dict(get_block_by_height(height, from_endpoint)["result"])
    return certificate

def get_inclusion_proof(queryKeys: list[str], endpoint: str = "") -> dict:
    return node_request("state_prove", params={"queryKeys": queryKeys}, endpoint=endpoint)

def send_transaction(hex_trs: str | bytes, endpoint: str = "") -> dict:
    if isinstance(hex_trs, bytes):
        hex_trs = hex_trs.hex()
    try:
        return node_request(RPC_REQUEST.POST_TRANSACTION, {"transaction": f"{hex_trs}"}, endpoint)
    except Exception as e:
        print(f"Error sending transaction: {e}")
        return {}

