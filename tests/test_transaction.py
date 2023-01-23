import json
import requests
from dingus.network.constants import RPC_ENDPOINTS
from dingus.types.transaction import Transaction
from dingus.types.keys import PrivateKey
import os
import dingus.codec as codec
import dingus.utils as utils
import dingus.network.api as api
import dingus.crypto as crypto


def test_register_mainchain_transaction():
    os.environ[
        "CHAIN_ID"
    ] = "00000123"
    os.environ[
        "NETWORK"
    ] = "devnet"

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
                {
                    "blsKey": bytes.fromhex("817a75cc65a459b31ad99fd060c4ff8d60db9bf76fa9fad8f045d96681b662af82dbaa8e76976dd34b8c2fcf7a2af71f"), 
                    "bftWeight": 500
                },
                {
                    "blsKey": bytes.fromhex("843cb4481c3ef4e7ac2b6ad1a1d7a05b92243911ae13a2cc5ad401ba9aae487910a61bb6a8b122892c809c8ed0d07278"), 
                    "bftWeight": 500
                },
                {
                    "blsKey": bytes.fromhex("a9fad83bbc2f09e9e1204b3485209f9b0cc838f5fca6ddbc06deaef31151fdbe8c50d92fec82da0e8a5a361030f542e8"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("96f6bf38f3224b50d009b9041ed3d4a198c85b9dbf5e9199798377a6d45f1186c92236bb00246dbee9fecc28f03f625a"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("b4784434b67d9d941a2fbce2835ff992c489799b7a9137de47a82e90eb27a21f38d5aa04fcb682e1ea324794b7e867c4"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("b02658bf33c9b8f83e84aba31c0e88dfcc17b5292f797a58d62488ac29cde4194eed736c3f6f44266e2ae4290daf2a95"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("a85cf5e59f43a916b54342b47596189b0bb5fa480c6e4820d3b837bf8aaed29f34cbcdf765393e76d1c5766b4ceb945b"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("a344973acb9fe51fd42fe501a063605db1b5f1cc0173c33adb6aa3510d07f86b9b60ca1a1001a710d58292bc22ada443"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("ad71f1e8a39393e59e030cc3906810990ff6a7fec210e3deb474d7cc292257d4f6a3cd090711334442a90d86b515bcc2"), 
                    "bftWeight": 450
                },
                {
                    "blsKey": bytes.fromhex("a14970a3a2e779a7ad9fafdcea4123f5c97f9f5ea86a7a2f378e3a38aa224f5903a55fd293cb5cf4c5600bf57446fb93"), 
                    "bftWeight": 450
                },
                {
                    "blsKey": bytes.fromhex("93f99b592a290c00b8cde4a3bb067e1da97331889c204fe67014be5e81d6013aa2b99e279642f6681becd3232574ede5"), 
                    "bftWeight": 450
                },
                {
                    "blsKey": bytes.fromhex("9778c9cbb5edc33a077627ff3311765ea8d47fdf89e26fcee2ac2da9faffd0cc2cd89c300cf045891e4a7d3e9bb3ba2b"), 
                    "bftWeight": 470
                },
                {
                    "blsKey": bytes.fromhex("a9baab9c029e3e8cdf81d1314223545226d6a2e5fee0f73c3307843f530a93b341398c3291d57d34e84474f7506bd525"), 
                    "bftWeight": 450
                },
                {
                    "blsKey": bytes.fromhex("ac6b46d7db66fe40676c12295fc95a1b5ee51a2f4f52ba5832a4e884fd726196d4736a563cbda3195135acf65176a488"), 
                    "bftWeight": 495
                },
                {
                    "blsKey": bytes.fromhex("a49ee8645edb3842760c799182f0d5fc3b15cddbe2f9303b360a80002dd01afb5cf1a53b0b11fc3f46b418101a09f717"), 
                    "bftWeight": 470
                },
                {
                    "blsKey": bytes.fromhex("82decaf528a5308e828b22f02c69a7f80e8c93602eb78d84b30b038aca38f57eec23fd97de3643c6bbd918e51ba6f401"), 
                    "bftWeight": 480
                },
                {
                    "blsKey": bytes.fromhex("b629cccdbda7c5acb2d1507f02d13b37944382547fbe87179a7a1663b266ca7dbf87f97c2ade69ff8c1d1f4e09fbe6f4"), 
                    "bftWeight": 480
                },
                {
                    "blsKey": bytes.fromhex("8f9b4bf3e8a1dde2b65fa255f577bbb57f521d01468c52bba14356cf134231f3306abc1e25ae55a8f86c9461c916c40f"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("b2f51fe4a22f725160e60d9422e0472621bee3322b7895ad81aebfec3aaaee17f32b0613239d8010b6660492987657f2"), 
                    "bftWeight": 450
                },
                {
                    "blsKey": bytes.fromhex("8b9c486088c1b4595b941496d0b14487a4e5575685c628f8e3bcdeb92366c9ef5fff903ed56d89a49ac6cfde9dd81c55"), 
                    "bftWeight": 490
                },
                {
                    "blsKey": bytes.fromhex("94f216e0411c495d61c549529a8f260323300efabce2c917910377a56b2384f1dc4f21078f97774f9fc67cc28f2a0e9f"), 
                    "bftWeight": 480
                }
            ],
            "mainchainCertificateThreshold": 6697, 
            "signature": "",
            "aggregationBits": ""
        }
    }

    params["params"]["mainchainValidators"] = sorted(params["params"]["mainchainValidators"], key=lambda x: x["blsKey"])
    # for x in params["params"]["mainchainValidators"]:
    #     print(f'''
    #     {{
    #         "blsKey": "{x["blsKey"].hex()}",
    #         "bftWeight": {x["bftWeight"]}
    #     }},
    # ''', end="")
    print("total bft weight", sum([x["bftWeight"] for x in params["params"]["mainchainValidators"]]))
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
    sidechain_validator_priv_keys = sorted([bytes.fromhex(v['plain']["blsPrivateKey"]) for v in validators_data["keys"]])
    sidechain_validator_pub_keys = sorted([bytes.fromhex(v['plain']["blsKey"]) for v in validators_data["keys"]])
    tag = "LSK_CHAIN_REGISTRATION_".encode('ascii')
    chainID = params["params"]["ownChainID"]
    message = reg_message.SerializeToString()
    signatures = [signBLS(sk, tag, chainID, message) for sk in sidechain_validator_priv_keys]
    agg_bits, signature = createAggSig(sidechain_validator_pub_keys, [(pub, sig) for pub, sig in zip(sidechain_validator_pub_keys, signatures)])
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
    os.environ[
        "CHAIN_ID"
    ] = "00000000"

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
                    "blsKey": bytes.fromhex("a16c45e64cdff30b177b08359f7af1a7265de199ee64c830406b4914b437da323d25601c7a8adcf752e0c891ca8dc06c"), 
                    "bftWeight": 5000
                },
                {
                    "blsKey": bytes.fromhex("b5d86b29e9f5a069167539b3c330d811192b90a1d4ab205f967b0ab9c8c08df55d108f9b2a383f4484f60895bf7e1339"), 
                    "bftWeight": 5000
                }
            ],
            "sidechainCertificateThreshold": 8000
        }
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



def rpc_post_trs(trs_bytes: str | bytes) -> dict:
    if isinstance(trs_bytes, bytes):
        trs_bytes = trs_bytes.hex()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "txpool_postTransaction",
        "params": {
            "transaction": trs_bytes
        }
    }
    net = os.environ["NETWORK"]
    endpoint = RPC_ENDPOINTS[net]
    url = f"{endpoint}/rpc"
    print("URL", url)
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    r = requests.get(url, headers=headers, json=payload)
    return r.json()
    
def test_send_transaction():
    os.environ[
        "CHAIN_ID"
    ] = "00000000"
    os.environ[
        "NETWORK"
    ] = "devnet"

    params = {
        "module": "token",
        "command": "transfer",
        "senderPublicKey": bytes.fromhex("43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73"),
        "nonce": 5,
        "fee": 1216299416,
        "params": {
            "tokenID": bytes.fromhex("0000000000000000"),
            "amount": 123986407700,
            "recipientAddress": bytes.fromhex("2ca4b4e9924547c48c04300b320be84e8cd81e4a"),
            "data": "Odi et amo. Quare id faciam, fortasse requiris."
        },
    }

    trs = Transaction.from_dict(params)
    sk1 = PrivateKey(bytes.fromhex("4cf6720801a87c4f9a4f8269671bff116d9af98734cae22315155d357f8b8510"))
    sk2 = PrivateKey(bytes.fromhex("c6bb32474a51daf65478204cb7cb554e7dbb7f7d44def985db56c925fd3f0859"))
    # print("unsigned trs:", trs.bytes.hex())
    # "private_key": "c6bb32474a51daf65478204cb7cb554e7dbb7f7d44def985db56c925fd3f0859", "public_key": "5f40d1f7a4e57ff921f5b06788877e85070f1f7bc382d293a43b79935048aed3"
    # "private_key": "4cf6720801a87c4f9a4f8269671bff116d9af98734cae22315155d357f8b8510", "public_key": "43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73"
    assert trs.bytes == trs.unsigned_bytes
    print("unsigned bytes:",trs.bytes.hex())
    trs.sign(sk1)
    trs.sign(sk2)
    print("signed trs:",trs)
    print("signed bytes:",trs.bytes.hex())
    print("ID", trs.id.hex())

    # ret = rpc_post_trs(trs.bytes.hex())

    # print(ret)

def get_validators_keys_from_file():
    validators_data = json.loads(open("./dev-validators.json", "r").read())
    # print (validators_data["keys"])
    validator_keys = sorted([bytes.fromhex(v['plain']["blsKey"]) for v in validators_data["keys"]])
    print(validator_keys)

if __name__ == "__main__":
    test_send_transaction()


#\"params\": { \"transaction\": \"0a036c6e731208726567697374657218002080cab5ee012a200c4862e7a9e80699b0d997a16336563fad3957bed28b09f7f8ed645827af0f9c320e0a07626c612e6c736b10d83618023a40006ab73f5ed3dd0f5008575525154f22226cec78d86b57ddd0b83af7a7d386ea6db581afd7f536e325a231bcf910d622253b3c3b5bd89f6df5f46eb51285af05\" }\n}",

# "http://localhost:7887/rpc",


