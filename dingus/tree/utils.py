from typing import Any, Callable
import math
from .constants import EMPTY_HASH, LEAF_PREFIX, BRANCH_PREFIX
from dingus.utils import hash


def merkle_root(data: list[bytes]) -> bytes:
    """Returns the Merkle root from a list of bytes as specified in https://github.com/LiskHQ/lips/blob/main/proposals/lip-0031.md#merkle-root

    Args:
        data (list[bytes]): input list

    Returns:
        bytes: Merkle root
    """

    size = len(data)
    if size == 0:
        return EMPTY_HASH
    if size == 1:
        return hash(LEAF_PREFIX + data[0])

    # Largest power of two smaller than size
    k = 2 << (math.floor(math.log2(size - 1)))
    # Split the data array into 2 subtrees. leftTree from index 0 to index k (not included), rightTree for the rest
    leftTree = data[:k]
    rightTree = data[k:]
    return hash(BRANCH_PREFIX + merkle_root(leftTree), merkle_root(rightTree))


def split_index(keys: list[bytes], condition: Callable) -> int:
    for idx, key in enumerate(keys):
        if condition(key):
            return idx
    return len(keys)


def split_keys_index(keys: list[bytes], byte_idx: int, target: int) -> int:
    for idx, k in enumerate(keys):
        if k[byte_idx] > target:
            return idx
    return len(keys)


def is_bit_set(bits: bytes, i: int) -> bool:
    shifted = bits[i // 8] << (i % 8)
    BIT_COMP = int.from_bytes(b"\x80", "big")
    return (shifted & BIT_COMP) == BIT_COMP


def key_to_bin(key: bytes, idx: int) -> int:
    return key[idx]


def binary_expansion(key: bytes):
    return f"{int.from_bytes(key, 'big'):0{8*len(key)}b}"


def binary_search(array: list, callback: Callable[[Any], bool]) -> int:
    lo = -1
    hi = len(array)
    while 1 + lo < hi:
        mi = lo + ((hi - lo) >> 1)
        if callback(array[mi]):
            hi = mi
        else:
            lo = mi
    return hi
