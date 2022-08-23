from __future__ import annotations
from hashlib import sha256
import os
import pyperclip
from pathlib import Path

from blspy import (
    BasicSchemeMPL,
    G1Element,
    G2Element,
    PopSchemeMPL,
    PrivateKey,
)

import dingus.types.keys as keys
import dingus.types.account as account
from dingus.constants import (
    ADDRESS_LENGTH,
    PUB_KEY_LENGTH,
    SEED_LENGTH,
    LISK32_CHARSET,
    DEFAULT_LISK32_ADDRESS_PREFIX,
    LISK32_ADDRESS_LENGTH,
)


def passphrase_to_private_key(passphrase: str) -> keys.PrivateKey:
    seed = sha256(passphrase.encode()).digest()
    return keys.PrivateKey(seed)


def hash(msg: bytes) -> bytes:
    return sha256(msg).digest()


def sign(msg: bytes, sk: keys.PrivateKey) -> bytes:
    return sk.sign(msg).signature

def tagMessage(tag: bytes, chainID: bytes, message: bytes) -> bytes:
    return tag + chainID + message


def signBLS(sk: PrivateKey, tag: bytes, chainID: bytes, message: bytes) -> G2Element:
    taggedMessage = tagMessage(tag, chainID, message)
    sig = PopSchemeMPL.sign(sk, hash(taggedMessage))
    assert sig == G2Element.from_bytes(bytes(sig))
    return sig

def verifyBLS(pk: G1Element, tag: bytes, chainID: bytes, message: bytes, sig: G2Element) -> bool:
    taggedMessage = tagMessage(tag, chainID, message)
    return PopSchemeMPL.verify(pk, hash(taggedMessage), sig)

def random_address() -> keys.Address:
    return keys.Address(os.urandom(ADDRESS_LENGTH))


def random_public_key() -> keys.PublicKey:
    return keys.PublicKey(os.urandom(PUB_KEY_LENGTH))


def random_private_key() -> keys.PrivateKey:
    return keys.PrivateKey(os.urandom(SEED_LENGTH))


def delete_account(filename: str) -> None:
    filename = f"{os.environ['BASE_PATH']}/accounts/{filename}"
    Path(filename).unlink(missing_ok=True)


def get_accounts_from_files() -> dict[str : account.Account]:
    accounts = {}
    account_files = os.listdir(f"{os.environ['BASE_PATH']}/accounts")
    for filename in account_files:
        try:
            act = account.Account.from_file(filename)
        except:
            continue

        if not act:
            continue

        accounts[act.address] = act

    return accounts


def copy_to_clipboard(text: str) -> None:
    pyperclip.copy(text)


def convert_uint_array(
    uint_array: list[int], from_bits: int, to_bits: int
) -> list[int]:
    max_value = (1 << to_bits) - 1
    accumulator = 0
    bits = 0
    result = []
    for p in range(len(uint_array)):
        byte = uint_array[p]
        # check that the entry is a value between 0 and 2^frombits-1
        if byte < 0 or byte >> from_bits != 0:
            return []

        accumulator = (accumulator << from_bits) | byte
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            result.append((accumulator >> bits) & max_value)

    return result


def convert_uint5_to_base32(uint5_array: list[int]) -> str:
    return "".join([LISK32_CHARSET[val] for val in uint5_array])


def polymod(uint5_array: list[int]) -> int:
    GENERATOR = [
        int("0x3b6a57b2", 16),
        int("0x26508e6d", 16),
        int("0x1ea119fa", 16),
        int("0x3d4233dd", 16),
        int("0x2a1462b3", 16),
    ]
    chk = 1
    for value in uint5_array:
        top = chk >> 25
        chk = ((chk & int("0x1ffffff", 16)) << 5) ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= GENERATOR[i]

    return chk


def create_checksum(uint5_array: list[int]) -> list[int]:
    values = uint5_array + [0, 0, 0, 0, 0, 0]
    mod = polymod(values) ^ 1
    result = []
    for p in range(6):
        result.append((mod >> (5 * (5 - p))) & 31)
    return result


def verify_lisk32_checksum(integer_sequence: list[int]) -> bool:
    return polymod(integer_sequence) == 1


def address_to_lisk32(address: bytes) -> str:
    uint5_address = convert_uint_array(address, 8, 5)
    uint5_checksum = create_checksum(uint5_address)
    return DEFAULT_LISK32_ADDRESS_PREFIX + convert_uint5_to_base32(
        uint5_address + uint5_checksum
    )


def validate_lisk32_address(address: str, prefix=DEFAULT_LISK32_ADDRESS_PREFIX) -> bool:
    if len(address) != LISK32_ADDRESS_LENGTH:
        return False

    if not address.startswith(DEFAULT_LISK32_ADDRESS_PREFIX):
        return False

    address_substring_array = address[len(DEFAULT_LISK32_ADDRESS_PREFIX) :]

    for char in address_substring_array:
        if char not in LISK32_CHARSET:
            return False

    integer_sequence = [LISK32_CHARSET.find(char) for char in address_substring_array]

    return verify_lisk32_checksum(integer_sequence)


def get_address_from_lisk32_address(base32_address: str) -> bytes:
    if not validate_lisk32_address(base32_address, DEFAULT_LISK32_ADDRESS_PREFIX):
        return b""

    # Ignore lsk prefix and checksum
    address_substring_array = base32_address[len(DEFAULT_LISK32_ADDRESS_PREFIX) : -6]
    integer_sequence = [LISK32_CHARSET.find(char) for char in address_substring_array]

    return bytes(convert_uint_array(integer_sequence, 5, 8))
