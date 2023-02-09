from __future__ import annotations
from hashlib import sha256
import math
import blspy as bls

import unicodedata
import hashlib

def normalize_string(txt: str | bytes) -> str:
    if isinstance(txt, bytes):
        utxt = txt.decode("utf8")
    elif isinstance(txt, str):
        utxt = txt
    else:
        raise TypeError("String value expected")

    return unicodedata.normalize("NFKD", utxt)

def passphrase_to_seed(passphrase: str, password: str ="") -> bytes:
    PBKDF2_ROUNDS = 2048
    passphrase = normalize_string(passphrase)
    password = normalize_string(password)
    password = "mnemonic" + password
    passphrase_bytes = passphrase.encode("utf-8")
    password_bytes = password.encode("utf-8")
    stretched = hashlib.pbkdf2_hmac(
        "sha512", passphrase_bytes, password_bytes, PBKDF2_ROUNDS
    )
    return stretched[:64]

def hash(msg: bytes) -> bytes:
    return sha256(msg).digest()

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