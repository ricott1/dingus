from dingus.types.transaction import Transaction
from dingus.types.keys import PrivateKey
import os

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
            "data": "Odi et amo. Quare id faciam, fortasse requiris.",
        },
        "signatures": [],
    }

    os.environ["CHAIN_ID"] = "00000000"
    trs = Transaction.from_dict(params)
    trs.sign(priv_key1)
    trs.sign(priv_key2)
    return trs

def unlockTest() -> Transaction:
    priv_key1 = PrivateKey(bytes.fromhex("4cf6720801a87c4f9a4f8269671bff116d9af98734cae22315155d357f8b8510"))

    params = {
        "module": "legacy",
        "command": "unlockTest",
        "nonce": "0",
        "fee": "1000000",
        "senderPublicKey": bytes.fromhex("43e59548e356f581251041dc922b8e27b7bc5fd37b33e7939422db82e29c9d73"),
        "params": {},
        "signatures": [],
    }

    trs = Transaction.from_dict(params)
    # trs.sign(priv_key1, bytes.fromhex("00000000"))
    return trs

