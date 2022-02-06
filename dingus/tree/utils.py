from typing import Callable
from .constants import EMPTY_HASH
from .types import LeafNode, BranchNode
import math


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
        return LeafNode(b"", data[0]).hash

    # Largest power of two smaller than size
    k = 2 << (math.floor(math.log2(size - 1)))
    # Split the data array into 2 subtrees. leftTree from index 0 to index k (not included), rightTree for the rest
    leftTree = data[:k]
    rightTree = data[k:]
    return BranchNode(merkle_root(leftTree), merkle_root(rightTree)).hash


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
    return (shifted & BIT_COMP) == BIT_COMP


def key_to_bin(key: bytes, idx: int) -> int:
    return key[idx]


BIT_COMP = int.from_bytes(b"\x80", "big")
