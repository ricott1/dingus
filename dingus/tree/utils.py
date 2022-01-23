from typing import Callable
from .constants import DEFAULT_KEY_LENGTH, EMPTY_HASH, LEAF_PREFIX, NODE_HASH_SIZE
from .types import LeafNode, BranchNode
import math

def merkle_root(data: list[bytes]) -> bytes:
    """
    As specified in https://github.com/LiskHQ/lips/blob/main/proposals/lip-0031.md#merkle-root
    """

    size = len(data)
    if size == 0: 
        return EMPTY_HASH
    if size == 1: 
        return LeafNode(b"", data[0]).hash
    
    # Largest power of two smaller than size
    k = 2**(math.floor(math.log2(size - 1)))
    # Split the data array into 2 subtrees. leftTree from index 0 to index k (not included), rightTree for the rest
    leftTree = data[0:k]
    rightTree = data[k:size]
    return BranchNode(merkle_root(leftTree), merkle_root(rightTree)).hash

def parse_leaf_data(data: bytes, keyLength: int) -> tuple[bytes, bytes]:
    key = data[len(LEAF_PREFIX):keyLength + len(LEAF_PREFIX)]
    value = data[keyLength + len(LEAF_PREFIX):]
    return (key, value)

def parse_branch_data(data: bytes) -> tuple[bytes, bytes]:
    left_hash = data[-2 * NODE_HASH_SIZE: -1 * NODE_HASH_SIZE]
    right_hash = data[-1 * NODE_HASH_SIZE:]
    return (left_hash, right_hash)

def split_keys(keys: list[bytes], condition: Callable) -> int:
    for idx, key in enumerate(keys):
        if condition(key):
            return idx
    return len(keys)

def is_bit_set(bits: bytes, i: int) -> bool:
    shifted = bits[i//8]<<(i % 8)
    return (shifted&BIT_COMP) == BIT_COMP

BIT_COMP = int.from_bytes(b"\x80", "big")