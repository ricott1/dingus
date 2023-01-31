import json
from dingus.types.transaction import Transaction
from dingus.types.keys import PrivateKey, PublicKey, Address
from google.protobuf.json_format import  ParseDict
import os
from dingus.codec.utils import normalize_bytes
import dingus.utils as utils
import dingus.network.api as api


def register_mainchain():
    mainchain_validators, mainchain_certificate_threshold = api.get_last_bft_params("https://lisk.frittura.org")
    mainchain_validators = sorted(mainchain_validators, key=lambda v: v["blsKey"])
    nonce = int(api.get_auth_account(sidechain_key.to_public_key().to_address().to_lsk32())["result"]["nonce"])
    params = {
        "module": "interoperability",
        "command": "registerMainchain",
        "nonce": nonce,
        "fee": 7350000,
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
    reg_mainchain_validators, reg_mainchain_certificate_threshold = api.get_last_bft_params("https://lisk.frittura.org")
    reg_mainchain_validators = sorted(reg_mainchain_validators, key=lambda v: v["blsKey"])
    reg_message_params = {
        "ownChainID": params["params"]["ownChainID"],
        "ownName": params["params"]["ownName"],
        "mainchainValidators": reg_mainchain_validators,
        "mainchainCertificateThreshold": reg_mainchain_certificate_threshold,
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
    sidechain_validators, sidechain_certificate_threshold = api.get_last_bft_params()

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
    trs.sign(sidechain_key)
    return trs

def register_sidechain() -> Transaction:
    sidechain_validators, sidechain_certificate_threshold = api.get_last_bft_params("http://localhost:7887")
    sidechain_validators = sorted(sidechain_validators, key=lambda x: x["blsKey"])
    nonce = int(api.get_auth_account(mainchain_key.to_public_key().to_address().to_lsk32())["result"]["nonce"])
    params = {
        "module": "interoperability",
        "command": "registerSidechain",
        "nonce": nonce,
        "fee": 1515000000,
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
    trs.sign(mainchain_key)
    return trs

def token_transfer() -> Transaction:
    if os.environ["CHAIN_ID"].endswith("000000"):
        priv_key = mainchain_key
    else:
        priv_key = sidechain_key
    pub_key = priv_key.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32())["result"]["nonce"])
    params = {
        "module": "token",
        "command": "transfer",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 26299416,
        "params": {
            "tokenID": bytes.fromhex(os.environ["CHAIN_ID"] + "00000000"),
            "amount": 500000000000,
            "recipientAddress": gregorio,
            "data": "Un dono per Gregoriello.",
        },
        "signatures": []
    }
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
    os.environ["CHAIN_ID"] = "04000000" #mainchain
    # os.environ["CHAIN_ID"] = "04000123" #sidechain
    # trs = register_sidechain()
    # print("signed trs:", trs)
    # print("\nID:", trs.id.hex())
    # trs.send()
    print("\n\n", json.dumps(api.get_last_finalized_block(), indent=4))
    # print("events 3308\n\n", json.dumps(api.get_events_by_height(837)["result"], indent=4))
    # print("auth", json.dumps(api.get_auth_account("lskduq5evojpfuephanymmmw55umt8yajow33bmtm")["result"], indent=4))