from __future__ import annotations
from hashlib import sha256
import math
import os
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

def signBLS(sk: bls.PrivateKey | bytes, tag: bytes, chainID: bytes, message: bytes) -> bls.G2Element:
    if isinstance(sk, bytes):
        sk = bls.PrivateKey.from_bytes(sk)
    sig = bls.PopSchemeMPL.sign(sk, hash(tag + chainID + message))
    return sig

def verifyBLS(pk: bls.G1Element, tag: bytes, chainID: bytes, message: bytes, sig: bls.G2Element) -> bool:
    return bls.PopSchemeMPL.verify(pk, hash(tag + chainID + message), sig)

def createAggSig(pub_key_list: list[bls.G1Element], pub_key_signature_pairs: list[tuple[bls.G1Element, bls.G2Element]]) -> tuple[bytes, bls.G2Element]:
    # aggregationBits = byte string of length ceil(length(keyList)/8) with all bytes set to 0
    aggregationBits = bytearray(math.ceil(len(pub_key_list) / 8))
    signatures = []
    for pair in pub_key_signature_pairs:
        signatures.append(pair[1])
        index = pub_key_list.index(pair[0])
        # set bit at position index to 1 in aggregationBits
        aggregationBits[index // 8] |= 1 << (index % 8)
    signature = bls.PopSchemeMPL.aggregate(signatures)
    return (aggregationBits, signature)

def verifyAggSig(keysList: list[bls.G1Element], aggregationBits: bytes, signature: bytes, tag: bytes, chainID: bytes, message: bytes) -> bool:
    hashedMessage = hash(tag + chainID + message)
    keys = []
    for i in range(8 * len(aggregationBits)):
        # if i-th bit of aggregationBits == 1
        if (aggregationBits[i // 8] >> (i % 8)) & 1:
            if isinstance(keysList[i], bytes):
                keys.append(bls.G1Element.from_bytes(keysList[i]))
            elif isinstance(keysList[i], bls.G1Element):
                keys.append(keysList[i])

    return bls.PopSchemeMPL.fast_aggregate_verify(keys, hashedMessage, bls.G2Element.from_bytes(signature))

def verifyWeightedAggSig(keysList: list[bls.G1Element], aggregationBits: bytes, signature: bytes, tag: bytes, chainID: bytes, weights: list[int], threshold: int, message: bytes) -> bool:
    hashedMessage = hash(tag + chainID + message)
    keys = []
    weightSum = 0
    # print()
    # print("Debugging aggr sign")
    # print("Message: ", tag.hex(), chainID.hex(), message.hex(), hashedMessage.hex())
    # print("Weight sum: ", weightSum)
    # print("Threshold: ", threshold)
    # print("Aggregation bits: ", aggregationBits.hex(), bin(int(aggregationBits.hex(), base=16))[2:])
    # print("Signature: ", signature.hex())
    # print("keys: ", len(keysList))
    # print("Verify", bls.PopSchemeMPL.fast_aggregate_verify(keys, hashedMessage, bls.G2Element.from_bytes(signature)))
    # print()
        
    for i in range(8 * len(aggregationBits)):
        # if i-th bit of aggregationBits == 1
        if (aggregationBits[i // 8] >> ((i % 8))) & 1:
            if isinstance(keysList[i], bytes):
                keys.append(bls.G1Element.from_bytes(keysList[i]))
            elif isinstance(keysList[i], bls.G1Element):
                keys.append(keysList[i])
            weightSum += weights[i]

    if weightSum < threshold:
        return False
    return bls.PopSchemeMPL.fast_aggregate_verify(keys, hashedMessage, bls.G2Element.from_bytes(signature))

def get_random_BLS_sk(seed: bytes = b"") -> tuple[bls.PrivateKey, bls.G2Element]:
    if seed == b"":
        seed = os.urandom(32)
    sk = bls.PopSchemeMPL.key_gen(seed)
    pop = bls.PopSchemeMPL.pop_prove(sk)
    return (sk, pop)