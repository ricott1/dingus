import json
from typing import Any
import requests
from dingus.network.constants import RPC_REQUEST
from dingus.types.transaction import Transaction
from dingus.types.keys import PrivateKey, PublicKey, Address
from google.protobuf.json_format import  ParseDict
import os
import dingus.codec as codec
from dingus.codec.utils import normalize_bytes
import dingus.utils as utils
import dingus.network.api as api
import dingus.crypto as crypto


def register_mainchain():
    mainchain_validators, mainchain_certificate_threshold = get_bft_params_from_endpoint()
    params = {
        "module": "interoperability",
        "command": "registerMainchain",
        "nonce": 0,
        "fee": 1438000,
        "senderPublicKey": sidechain_key.to_public_key(),
        "params": {
            "ownChainID": bytes.fromhex("04000123"),
            "ownName": "inverno",
            "mainchainValidators": mainchain_validators,
            "mainchainCertificateThreshold": mainchain_certificate_threshold,
            "signature": b"",
            "aggregationBits": b"",
        },
        "signatures": []
    }

    from dingus.application.interoperability.schemas import proto

    reg_message = proto["mainchainRegistrationMessage"]()
    reg_message_params = {
        "ownChainID": params["params"]["ownChainID"],
        "ownName": params["params"]["ownName"],
        "mainchainValidators": params["params"]["mainchainValidators"],
        "mainchainCertificateThreshold": params["params"]["mainchainCertificateThreshold"],
    }

    reg_message = ParseDict(normalize_bytes(reg_message_params), reg_message)

    from dingus.crypto import signBLS, createAggSig

    validators_data = json.loads(open("./interop_testing/inverno/dev-validators.json", "r").read())
    sidechain_validator_keys = [
        {
            "blsKey": bytes.fromhex(v["plain"]["blsKey"]),
            "blsPrivateKey": bytes.fromhex(v["plain"]["blsPrivateKey"]),
        } for v in validators_data["keys"]
    ]
    sidechain_validators, sidechain_certificate_threshold = get_bft_params_from_endpoint("http://localhost:7887")
    tag = "LSK_CHAIN_REGISTRATION_".encode("ascii")
    chainID = params["params"]["ownChainID"]
    message = reg_message.SerializeToString()
    keys_and_signatures = []
    for v in sidechain_validators:
        bls_key = v["blsKey"]
        validator = next(u for u in sidechain_validator_keys if u["blsKey"].hex() == bls_key.hex())
        bls_priv_key = validator["blsPrivateKey"]
        keys_and_signatures.append((bls_key, signBLS(bls_priv_key, tag, chainID, message)))

    keys_and_signatures = sorted(keys_and_signatures, key=lambda x: x[0])
    agg_bits, signature = createAggSig(
        [k for k, _ in keys_and_signatures],
        keys_and_signatures,
    )
    params["params"]["aggregationBits"] = bytes(agg_bits)
    params["params"]["signature"] = bytes(signature)

    trs = Transaction.from_dict(params)
    os.environ["CHAIN_ID"] = "04000123"
    trs.sign(sidechain_key)

    return trs


def register_sidechain() -> Transaction:
    sidechain_validators, sidechain_certificate_threshold = get_bft_params_from_endpoint("http://localhost:7887")
    params = {
        "module": "interoperability",
        "command": "registerSidechain",
        "nonce": 0,
        "fee": 1005000000,
        "senderPublicKey": mainchain_key.to_public_key(),
        "params": {
            "chainID": bytes.fromhex("04000123"),
            "name": "inverno",
            "sidechainValidators": sidechain_validators,
            "sidechainCertificateThreshold": sidechain_certificate_threshold,
        },
        "signatures": []
    }

    trs = Transaction.from_dict(params)
    os.environ["CHAIN_ID"] = "04000000"
    trs.sign(mainchain_key)

    # schema = codec.validators.Validators()
    # for v in params["params"]["sidechainValidators"]:
    #     val_schema = codec.validators.Validator()
    #     val_schema.blsKey = v["blsKey"]
    #     val_schema.bftWeight = v["bftWeight"]
    #     schema.validators.extend([val_schema])

    # schema.certificateThreshold = params["params"]["sidechainCertificateThreshold"]
    # print("validators hash", crypto.hash(schema.SerializeToString()).hex())
    
    return trs


def token_transfer() -> Transaction:
    priv_key = mainchain_key
    pub_key = priv_key.to_public_key()
    
    params = {
        "module": "token",
        "command": "transfer",
        "senderPublicKey": pub_key,
        "nonce": 5,
        "fee": 26299416,
        "params": {
            "tokenID": bytes.fromhex("0400000000000000"),
            "amount": 500000000000,
            "recipientAddress": gregorio,
            "data": "Un dono per Gregoriello.",
        },
        "signatures": []
    }
    os.environ["CHAIN_ID"] = "04000000"
    trs = Transaction.from_dict(params)
    trs.sign(priv_key)
    return trs

def lip68() -> Transaction:
    priv_key1 = PrivateKey(bytes.fromhex("4cf6720801a87c4f9a4f8269671bff116d9af98734cae22315155d357f8b8510"))
    priv_key2 = PrivateKey(bytes.fromhex("c6bb32474a51daf65478204cb7cb554e7dbb7f7d44def985db56c925fd3f0859"))

    params = {
        "module": "token",
        "command": "transfer",
        "nonce": "5",
        "fee": "1216299416",
        "senderPublicKey": bytes.fromhex("43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73"),
        "params": {
            "tokenID": bytes.fromhex("0000000000000000"),
            "amount": "123986407700",
            "recipientAddress": bytes.fromhex("2ca4b4e9924547c48c04300b320be84e8cd81e4a"),
            "data": "Odi et amo. Quare id faciam, fortasse requiris."
        },
        "signatures": []
    }

    os.environ["CHAIN_ID"] = "00000000"
    trs = Transaction.from_dict(params)
    trs.sign(priv_key1)
    trs.sign(priv_key2)
    return trs



def get_node_info(endpoint: str = "https://lisk.frittura.org") -> dict:
    if resp := api.rpc_request("system_getNodeInfo", endpoint=endpoint) and resp.status_code == 200:
        return resp.json()
    return {}

def get_validator(address: str, endpoint: str = "https://lisk.frittura.org") -> dict:
    if resp := api.rpc_request("validators_getValidator", params={"address": f"{address}"}, endpoint=endpoint) and resp.status_code == 200:
        return resp.json()
    return {}

def get_generator_list(height: int, endpoint: str = "https://lisk.frittura.org") -> dict:
    if resp := api.rpc_request("chain_getGeneratorList", params={"height": height}, endpoint=endpoint) and resp.status_code == 200:
        return resp.json()
    return {}

def get_bft_parameters(height: int, endpoint: str = "https://lisk.frittura.org") -> dict:
    if resp := api.rpc_request("consensus_getBFTParameters", params= {"height": height}, endpoint=endpoint) and resp.status_code == 200:
        return resp.json()
    return {}

def get_balance(address: str, endpoint: str = "https://lisk.frittura.org") -> dict:
    return api.rpc_request(RPC_REQUEST.GET_BALANCE, params={"address": f"{address}"}, endpoint=endpoint).json()

def get_bft_params_from_endpoint(endpoint: str = "https://lisk.frittura.org") -> tuple[list[dict[str, Any]], int]:
    if node_info := get_node_info(endpoint):
        finalized_height = node_info["result"]["finalizedHeight"]
    else:
        return ([], 0)
        
    bft_params = get_bft_parameters(finalized_height)["result"]
    validators = [
        { 
            "blsKey": bytes.fromhex(v["blsKey"]),
            "bftWeight": v["bftWeight"],
            
        } for v in bft_params["validators"]]
    threshold = bft_params["certificateThreshold"]
    return (validators, threshold)


def get_chain_validators_from_file(filename: str):
    validators_data = json.loads(open(filename, "r").read())
    bls_keys = sorted([bytes.fromhex(v["plain"]["blsKey"]) for v in validators_data["keys"]])
    
    return [
        {
            "blsKey": k,
            "bftWeight": 1,
        }
    for k in bls_keys]


mainchain_key = PrivateKey(bytes.fromhex("6a2ce559470d0e4b01a412c896b9d960b75cb6a54d30d548c4229c20ad0a07c9"))
sidechain_key = PrivateKey(bytes.fromhex("721d198cc3dcb8e4fd63123c05a72eb5451dbddcd2d4ae8fcd8f9e67bb3de2e8"))
gregorio = PublicKey(bytes.fromhex("67cb29899c1dc54486d600d1081162f7ea4cd9414de85b106dcb6be7b4ce074e")).to_address()
maxime = utils.get_address_from_lisk32_address("lskduq5evojpfuephanymmmw55umt8yajow33bmtm")

if __name__ == "__main__":
    # trs = register_sidechain()
    # print("signed trs:", trs)
    # print("\nID:", trs.id.hex())
    # trs.send()
    print(get_balance("lskduq5evojpfuephanymmmw55umt8yajow33bmtm"))

