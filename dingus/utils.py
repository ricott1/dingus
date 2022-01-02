# from nacl.hash import sha256 
from hashlib import sha256 
import os
import pyperclip

import dingus.types.keys as keys
from dingus.constants import ADDRESS_LENGTH, PUB_KEY_LENGTH, SEED_LENGTH, LSK32_CHARSET


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

def mock_block() -> dict:
    return{
        'id': '856ab6c964aae1b9ff42a3866defd871a8adf4169bd883d01abd205ee0e59ec2', 
        'height': 17281669, 
        'version': 2, 
        'timestamp': 1639824850, 
        'generatorAddress': 'lskbfur9zgv52sov3g44zgaepc9rkscgwtz69y3t2', 
        'generatorPublicKey': 'd76962002b6f39155251f759ec91e93c8dddba7d9df1a909937f265af606143b', 
        'generatorUsername': 'benevale', 
        'transactionRoot': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 
        'signature': 'f12ef06edc5c3237427b83b68a93cee7083c57a0c8c82a2b3ef0cb00129b3ce2a1e0cb4c5348efbd96d01804ac2cb29fe4cad68a51677ac7f531b008fddb6903', 
        'previousBlockId': '1be9ed7bea70de312490e87f0ac780632836f6e024dbff3ddeb0efb777ff9cca', 
        'numberOfTransactions': 0, 
        'totalForged': '100000000', 
        'totalBurnt': '0', 
        'totalFee': '0', 
        'reward': '100000000', 
        'isFinal': False, 
        'maxHeightPreviouslyForged': 17281623, 
        'maxHeightPrevoted': 17281586, 
        'seedReveal': '015d705212c99e897ce00d5a77eacef5'
        }

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
    return "".join([LSK32_CHARSET[val] for val in uint5_array])


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
    return "lsk" + convert_uint5_to_base32(uint5_address + uint5_checksum)
