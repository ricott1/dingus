import json
import requests
from dingus.network.constants import RPC_ENDPOINTS
from dingus.types.transaction import Transaction
from dingus.types.keys import PrivateKey, PublicKey
import os
import dingus.codec as codec
import dingus.utils as utils
import dingus.network.api as api
import dingus.crypto as crypto


def test_register_mainchain_transaction():
    params = {
        "module": "interoperability",
        "command": "registerMainchain",
        "nonce": 3,
        "fee": 1438000,
        "senderPublicKey": bytes.fromhex("43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73"),
        "params": {
            "ownChainID": bytes.fromhex("00000123"),
            "ownName": "hello_world!",
            "mainchainValidators": [
            ],
            "mainchainCertificateThreshold": 6697,
            "signature": "",
            "aggregationBits": "",
        },
    }

    params["params"]["mainchainValidators"] = sorted(params["params"]["mainchainValidators"], key=lambda x: x["blsKey"])
    # for x in params["params"]["mainchainValidators"]:
    #     print(f'''
    #     {{
    #         "blsKey": "{x["blsKey"].hex()}",
    #         "bftWeight": {x["bftWeight"]}
    #     }},
    # ''', end="")
    print(
        "total bft weight",
        sum([x["bftWeight"] for x in params["params"]["mainchainValidators"]]),
    )
    schema = codec.validators.Validators()
    for v in params["params"]["mainchainValidators"]:
        val_schema = codec.validators.Validator()
        val_schema.blsKey = v["blsKey"]
        val_schema.bftWeight = v["bftWeight"]
        schema.validators.extend([val_schema])

    schema.certificateThreshold = params["params"]["mainchainCertificateThreshold"]
    print("validators hash", crypto.hash(schema.SerializeToString()).hex())

    reg_message = codec.transaction.RegistrationSignatureMessage()
    reg_message.ownName = params["params"]["ownName"]
    reg_message.ownChainID = params["params"]["ownChainID"]
    for v in params["params"]["mainchainValidators"]:
        val_schema = codec.transaction.ChainValidator()
        val_schema.blsKey = v["blsKey"]
        val_schema.bftWeight = v["bftWeight"]
        reg_message.mainchainValidators.extend([val_schema])
    reg_message.mainchainCertificateThreshold = params["params"]["mainchainCertificateThreshold"]

    from dingus.crypto import signBLS, createAggSig

    validators_data = json.loads(open("./dev-validators.json", "r").read())
    sidechain_validator_priv_keys = sorted([bytes.fromhex(v["plain"]["blsPrivateKey"]) for v in validators_data["keys"]])
    sidechain_validator_pub_keys = sorted([bytes.fromhex(v["plain"]["blsKey"]) for v in validators_data["keys"]])
    tag = "LSK_CHAIN_REGISTRATION_".encode("ascii")
    chainID = params["params"]["ownChainID"]
    message = reg_message.SerializeToString()
    signatures = [signBLS(sk, tag, chainID, message) for sk in sidechain_validator_priv_keys]
    agg_bits, signature = createAggSig(
        sidechain_validator_pub_keys,
        [(pub, sig) for pub, sig in zip(sidechain_validator_pub_keys, signatures)],
    )
    params["params"]["aggregationBits"] = bytes(agg_bits)
    params["params"]["signature"] = bytes(signature)
    # print(params)

    trs = Transaction.from_dict(params)
    sk1 = PrivateKey(bytes.fromhex("4cf6720801a87c4f9a4f8269671bff116d9af98734cae22315155d357f8b8510"))

    trs.sign(sk1)
    print("\nsigned trs:", trs)
    print("\n", len(trs.bytes), "bytes:", trs.bytes.hex())
    print("\nID:", trs.id.hex())

    ret = rpc_post_trs(trs.bytes.hex())

    print(ret)


def test_register_sidechain_transaction():

    params = {
        "module": "interoperability",
        "command": "registerSidechain",
        "nonce": 0,
        "fee": 1005000000,
        "senderPublicKey": bytes.fromhex("5f40d1f7a4e57ff921f5b06788877e85070f1f7bc382d293a43b79935048aed3"),
        "params": {
            "name": "hello_world!",
            "chainID": bytes.fromhex("00000123"),
            "sidechainValidators": [
                {
                    "blsKey": bytes.fromhex(
                        "a16c45e64cdff30b177b08359f7af1a7265de199ee64c830406b4914b437da323d25601c7a8adcf752e0c891ca8dc06c"
                    ),
                    "bftWeight": 5000,
                },
                {
                    "blsKey": bytes.fromhex(
                        "b5d86b29e9f5a069167539b3c330d811192b90a1d4ab205f967b0ab9c8c08df55d108f9b2a383f4484f60895bf7e1339"
                    ),
                    "bftWeight": 5000,
                },
            ],
            "sidechainCertificateThreshold": 8000,
        },
    }

    trs = Transaction.from_dict(params)
    sk1 = PrivateKey(bytes.fromhex("c6bb32474a51daf65478204cb7cb554e7dbb7f7d44def985db56c925fd3f0859"))

    print("unsigned trs:", trs.bytes.hex())
    assert trs.bytes == trs.unsigned_bytes
    trs.sign(sk1)
    print("signed trs:", trs)
    print("bytes:", len(trs.bytes))
    print("ID:", trs.id.hex())

    schema = codec.validators.Validators()
    for v in params["params"]["sidechainValidators"]:
        val_schema = codec.validators.Validator()
        val_schema.blsKey = v["blsKey"]
        val_schema.bftWeight = v["bftWeight"]
        schema.validators.extend([val_schema])

    schema.certificateThreshold = params["params"]["sidechainCertificateThreshold"]
    print("validators hash", crypto.hash(schema.SerializeToString()).hex())


def rpc_post_trs(trs_bytes: str | bytes, endpoint: str = "") -> dict:
    if isinstance(trs_bytes, bytes):
        trs_bytes = trs_bytes.hex()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "txpool_postTransaction",
        "params": {"transaction": trs_bytes},
    }
    net = os.environ["NETWORK"]
    endpoint = RPC_ENDPOINTS[net] if not endpoint else endpoint
    url = f"{endpoint}/rpc"
    print("URL", url)
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    r = requests.get(url, headers=headers, json=payload)
    return r.json()


def test_send_transaction():
#     "publicKey": "c67c009e3df222fb6ad33e43907e94f7bf62f487e96fae2c54c53a7c5f11dbee",
#    "privateKey": "30bf2bbc8d728149b3822074d6d9e0219018f0649d21c2a633188c67a0d5da11c67c009e3df222fb6ad33e43907e94f7bf62f487e96fae2c54c53a7c5f11dbee",
#    "
    address = PublicKey(bytes.fromhex("43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73")).to_address()
    params = {
        "module": "token",
        "command": "transfer",
        "senderPublicKey": bytes.fromhex("c67c009e3df222fb6ad33e43907e94f7bf62f487e96fae2c54c53a7c5f11dbee"),
        "nonce": 1,
        "fee": 1216299416,
        "params": {
            "tokenID": bytes.fromhex("0004012300000000"),
            "amount": 1236407700,
            "recipientAddress": crypto.hash(address)[:20],
            "data": "Odi et amo. Quare id faciam, fortasse requiris.",
        },
    }

    trs = Transaction.from_dict(params)
    sk1 = PrivateKey(bytes.fromhex("30bf2bbc8d728149b3822074d6d9e0219018f0649d21c2a633188c67a0d5da11"))
    trs.sign(sk1)
    print("ID", trs.id.hex())

    ret = rpc_post_trs(trs.bytes.hex(), endpoint="https://lisk.frittura.org")
    # "https://xeimonas.frittura.org"
     
    print(ret)


def get_validators_keys_from_file():
    validators_data = json.loads(open("./dev-validators.json", "r").read())
    validator_keys = sorted([bytes.fromhex(v["plain"]["blsKey"]) for v in validators_data["keys"]])
    return validator_keys

def load_data_from_file():
    validators_data = json.loads(open("./dev-validators.json", "r").read())
    bls_keys = sorted([bytes.fromhex(v["plain"]["blsKey"]) for v in validators_data["keys"]])
    public_keys = sorted([bytes.fromhex(v["publicKey"]) for v in validators_data["keys"]])

# {
#    "address": "lskztwohp7mcyufou9cz67qr3vpn24b3oyqftfnbd",
#    "keyPath": "m/44'/134'/0'",
#    "publicKey": "43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73",
#    "privateKey": "4cf6720801a87c4f9a4f8269671bff116d9af98734cae22315155d357f8b851043e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73",
#    "plain": {
#     "generatorKeyPath": "m/25519'/134'/0'/0'",
#     "generatorKey": "ae2876df3d62bb32bd1048c1cd087c07d1031f3282bd608f342f64d952402574",
#     "generatorPrivateKey": "d667a233dae663c78c0c7bd7958a4c280e7780cc6b74ff9132919b9c71ec80f6ae2876df3d62bb32bd1048c1cd087c07d1031f3282bd608f342f64d952402574",
#     "blsKeyPath": "m/12381/134/0/0",
#     "blsKey": "836d30e43edabf4f60a09f5d4570911f25a9dcb1563f9e220a5f049bca52bdd02f6f58a35a93ca65a2852feadafb170d",
#     "blsProofOfPosession": "84b169ee81b56af8c49ca4a8d11df11f526bc0d612e179f525061dc113819444d7e9daf71ab85185c16478fb3a0b74f41696c403c05fbc3ec77ec5c7c1fdea9996cd690e944a61165c066f5f41aaf1d4d02e70d9e6f69ca2605b10479fd8c62f",
#     "blsPrivateKey": "274a6ed575bb69a0f6efa650dc3dd9e1ae80333e2a59145d0165c613447be999"
#    },

if __name__ == "__main__":
    os.environ["CHAIN_ID"] = "00040123"
    os.environ["NETWORK"] = "devnet"
    # get_validators_keys_from_file()
    test_send_transaction()
    # test_register_mainchain_transaction()


# \"params\": { \"transaction\": \"0a036c6e731208726567697374657218002080cab5ee012a200c4862e7a9e80699b0d997a16336563fad3957bed28b09f7f8ed645827af0f9c320e0a07626c612e6c736b10d83618023a40006ab73f5ed3dd0f5008575525154f22226cec78d86b57ddd0b83af7a7d386ea6db581afd7f536e325a231bcf910d622253b3c3b5bd89f6df5f46eb51285af05\" }\n}",

# "http://localhost:7887/rpc",


genesis config bftBatchSize pos.activeValidators/standbyValidators
genesis_asset.json init validators
./bin/run genesis-block:create --output config/default --assets-file ./config/default/genesis_assets.json 