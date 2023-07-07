import dingus.crypto as crypto
from ecpy.curves import Curve, Point
import json
from dingus import crypto
from dingus.types.transaction import Transaction
from dingus.types.keys import PrivateKey
import dingus.network.api as api

SIDECHAIN_ID = "03000042"
MAINCHAIN_ID = "03000000"
SIDECHAIN_NAME = "atomic_cloak"
LSK = 10**8

with open("sidechain/passphrase.json", "r") as f:
    sidechain_passphrase = json.load(f)["passphrase"]
sidechain_key_val = PrivateKey.from_passphrase(sidechain_passphrase)
mainchain_key_val = sidechain_key_val
user_key = PrivateKey(crypto.hash(bytes.fromhex("deadbeefc0feee")))
user_key2 = PrivateKey(crypto.hash(bytes.fromhex("deadbeefc0feeeee")))

sidechain_rpc_endpoint = "localhost:7887"


def commitment_from_point(qx: int, qy: int) -> bytes:
    swapID = int.from_bytes(crypto.keccak256(qx.to_bytes(32)+qy.to_bytes(32))) & 0x00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    return swapID.to_bytes(32, 'big')

def commitment_from_secret(s: bytes) -> Point:
    cv = Curve.get_curve('secp256k1')
    Gx = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
    Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
    G = Point(Gx, Gy, cv)
    Q = int.from_bytes(s)*G
    return commitment_from_point(Q.x, Q.y)

def openSwap(swapID: bytes) -> Transaction:
    priv_key = sidechain_key_val
    endpoint = sidechain_rpc_endpoint
    chainID = SIDECHAIN_ID

    pub_key = priv_key.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    last_block = api.get_last_block(endpoint)
    params = {
        "module": "atmen",
        "command": "openSwap",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 54300000,
        "params": {
            "swapID": swapID,
            "tokenID": bytes.fromhex(f"{chainID}00000000"),
            "value": 2*LSK,
            "recipientAddress": user_key2.to_public_key().to_address(),
            "timelock": last_block.header.timestamp + 1000,
            "tip": 0
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(params)
    print("trs:", trs)
    trs.sign(priv_key, bytes.fromhex(chainID))
    return trs

def closeSwap(swapID: bytes, secret: bytes) -> Transaction:
    priv_key = sidechain_key_val
    endpoint = sidechain_rpc_endpoint
    chainID = SIDECHAIN_ID

    pub_key = priv_key.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    params = {
        "module": "atmen",
        "command": "closeSwap",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 6000022,
        "params": {
            "swapID": swapID,
            "secret": secret,
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(params)
    print("trs:", trs)
    trs.sign(priv_key, bytes.fromhex(chainID))
    return trs

def redeemSwap(swapID: bytes) -> Transaction:
    priv_key = sidechain_key_val
    endpoint = sidechain_rpc_endpoint
    chainID = SIDECHAIN_ID

    pub_key = priv_key.to_public_key()
    nonce = int(api.get_auth_account(pub_key.to_address().to_lsk32(), endpoint)["result"]["nonce"])
    params = {
        "module": "atmen",
        "command": "redeemSwap",
        "senderPublicKey": pub_key,
        "nonce": nonce,
        "fee": 6000000,
        "params": {
            "swapID": swapID
        },
        "signatures": [],
    }
    trs = Transaction.from_dict(params)
    print("trs:", trs)
    trs.sign(priv_key, bytes.fromhex(chainID))
    return trs