from __future__ import annotations
from hashlib import sha256
import math
import blspy as bls

import dingus.types.keys as keys


def passphrase_to_private_key(passphrase: str) -> keys.PrivateKey:
    seed = sha256(passphrase.encode()).digest()
    return keys.PrivateKey(seed)

def hash(msg: bytes) -> bytes:
    return sha256(msg).digest()

def sign(msg: bytes, sk: keys.PrivateKey) -> bytes:
    return sk.sign(msg).signature

def tagMessage(tag: bytes, chainID: bytes, message: bytes) -> bytes:
    return tag + chainID + message

def signBLS(sk: bls.PrivateKey | bytes, tag: bytes, chainID: bytes, message: bytes) -> bls.G2Element:
    if isinstance(sk, bytes):
        sk = bls.PrivateKey.from_bytes(sk)
    taggedMessage = tagMessage(tag, chainID, message)
    sig = bls.PopSchemeMPL.sign(sk, hash(taggedMessage))
    assert sig == bls.G2Element.from_bytes(bytes(sig))
    return sig

def verifyBLS(pk: bls.G1Element, tag: bytes, chainID: bytes, message: bytes, sig: bls.G2Element) -> bool:
    taggedMessage = tagMessage(tag, chainID, message)
    return bls.PopSchemeMPL.verify(pk, hash(taggedMessage), sig)

def createAggSig(pub_key_list: list[bls.G1Element], pub_key_signature_pairs: list[tuple[bls.G1Element, bls.G2Element]]) -> tuple[bytes, bls.G2Element]:
    # aggregationBits = byte string of length ceil(length(keyList)/8) with all bytes set to 0
    aggregationBits = bytearray(math.ceil(len(pub_key_list) / 8))
    signatures = []
    for pair in pub_key_signature_pairs:
        signatures.append(pair[1])
        index = pub_key_list.index(pair[0])
        # set bit at position index to 1 in aggregationBits
        aggregationBits[index // 8] |= 1 << (index % 8)
    # signature = Aggregate(signatures)
    signature = bls.PopSchemeMPL.aggregate(signatures)
    return (aggregationBits, signature)