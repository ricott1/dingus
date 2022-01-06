# from nacl.hash import sha256 
from hashlib import sha256 
import os
import json
import pyperclip
from pathlib import Path
import logging

import dingus.types.keys as keys
from dingus.constants import ADDRESS_LENGTH, PUB_KEY_LENGTH, SEED_LENGTH, LISK32_CHARSET, DEFAULT_LISK32_ADDRESS_PREFIX, LISK32_ADDRESS_LENGTH


def passphrase_to_private_key(passphrase: str) -> keys.PrivateKey:
    seed = sha256(passphrase.encode()).digest()
    return keys.PrivateKey(seed)

def hash(msg: bytes) -> bytes:
    return sha256(msg).digest()

def sign(msg: bytes, sk: keys.PrivateKey) -> bytes:
    return sk.sign(msg).signature

def random_address() -> keys.Address:
    return keys.Address(os.urandom(ADDRESS_LENGTH))

def random_public_key() -> keys.PublicKey:
    return keys.PublicKey(os.urandom(PUB_KEY_LENGTH))

def random_private_key() -> keys.PrivateKey:
    return keys.PrivateKey(os.urandom(SEED_LENGTH)) 

def lisk32_to_avatar(base32_address: str) -> list[tuple[int]]:
    address = get_address_from_lisk32_address(base32_address)
    avatar = []
    r, g, b = [hash(bytes.fromhex(f"0{i}") + address) for i in range(3)]
    for i in range(0, len(r), 2):
        _r = int.from_bytes(r[i:i+1], "big")//16*16
        _g = int.from_bytes(g[i:i+1], "big")//16*16
        _b = int.from_bytes(b[i:i+1], "big")//16*16
        avatar.append((_r, _g, _b))
    return avatar

def save_account(filename: str, data: dict) -> None:
    if "balance" not in data:
        data["balance"] = 0
    if "public_key" not in data:
        data["public_key"] = ""
    else:
        data["public_key"] = data["public_key"].hex()
    if "nonce" not in data:
        data["nonce"] = 0
    if "name" not in data:
        data["name"] = ""
        
    if "ciphertext" in data \
        and "salt" in data \
        and "iv" in data \
        and "iteration_count" in data:
        data["bookmark"] = False
    else:
        data["bookmark"] = True

    try:
        with open(f"{os.environ['DINGUS_BASE_PATH']}/accounts/{filename}", "w") as f:
            f.write(json.dumps(data))
    except Exception as err:
        logging.error(f"utils.save_account {err}")
        raise err

def load_account(filename: str) -> dict:
    try:
        with open(f"{os.environ['DINGUS_BASE_PATH']}/accounts/{filename}", "r") as f:
            data = json.load(f)
    except Exception as err:
        logging.error(f"utils.load_account {err}")
        return {}

    if "address" not in data:
        return {}

    if "balance" not in data:
        data["balance"] = 0
    if "public_key" not in data:
        data["public_key"] = b""
    else:
        data["public_key"] = bytes.fromhex(data["public_key"])
    if "nonce" not in data:
        data["nonce"] = 0
    if "name" not in data:
        data["name"] = ""
        
    if "ciphertext" in data \
        and "salt" in data \
        and "iv" in data \
        and "iteration_count" in data:
        data["bookmark"] = False
    else:
        data["bookmark"] = True
    
    return data

def delete_account(filename: str) -> None:
    filename = f"{os.environ['DINGUS_BASE_PATH']}/accounts/{filename}"
    Path(filename).unlink(missing_ok=True)

def copy_to_clipboard(text: str) -> None:
    pyperclip.copy(text)

def convert_uint_array(uint_array: list[int], from_bits: int, to_bits: int) -> list[int]:
    max_value = (1 << to_bits) - 1
    accumulator = 0
    bits = 0
    result = []
    for p in range(len(uint_array)):
        byte = uint_array[p]
        # check that the entry is a value between 0 and 2^frombits-1
        if (byte < 0 or byte >> from_bits != 0):
            return []

        accumulator = (accumulator << from_bits) | byte
        bits += from_bits
        while (bits >= to_bits):
            bits -= to_bits
            result.append((accumulator >> bits) & max_value)

    return result

def convert_uint5_to_base32(uint5_array: list[int]) -> str:
    return "".join([LISK32_CHARSET[val] for val in uint5_array])


def polymod(uint5_array: list[int])-> int:
    GENERATOR = [
        int("0x3b6a57b2", 16), 
        int("0x26508e6d", 16), 
        int("0x1ea119fa", 16), 
        int("0x3d4233dd", 16), 
        int("0x2a1462b3", 16)
    ]
    chk = 1
    for value in uint5_array:
        top = chk >> 25
        chk = ((chk & int("0x1ffffff", 16)) << 5) ^ value
        for i in range(5):
            if ((top >> i) & 1):
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
    return DEFAULT_LISK32_ADDRESS_PREFIX + convert_uint5_to_base32(uint5_address + uint5_checksum)

def validate_lisk32_address(address: str, prefix = DEFAULT_LISK32_ADDRESS_PREFIX) -> bool:
    if len(address) != LISK32_ADDRESS_LENGTH:
        return False

    if not address.startswith(DEFAULT_LISK32_ADDRESS_PREFIX):
        return False

    address_substring_array = address[len(DEFAULT_LISK32_ADDRESS_PREFIX):]

    for char in address_substring_array:
        if char not in LISK32_CHARSET:
            return False

    integer_sequence = [LISK32_CHARSET.find(char) for char in address_substring_array]

    return verify_lisk32_checksum(integer_sequence)

def get_address_from_lisk32_address(base32_address: str) -> bytes:
    if not validate_lisk32_address(base32_address, DEFAULT_LISK32_ADDRESS_PREFIX):
        return b""
    
    # Ignore lsk prefix and checksum
    address_substring_array = base32_address[len(DEFAULT_LISK32_ADDRESS_PREFIX):-6]
    integer_sequence = [LISK32_CHARSET.find(char) for char in address_substring_array]

    return bytes(convert_uint_array(integer_sequence, 5, 8))
