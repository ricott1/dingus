from .constants import EMPTY_HASH, LEAF_PREFIX, NODE_HASH_SIZE
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
    key = data[len(LEAF_PREFIX):keyLength + len(LEAF_PREFIX) + 1]
    value = data[keyLength + len(LEAF_PREFIX) + 1:]
    return (key, value)

def parse_branch_data(data: bytes) -> tuple[bytes, bytes]:
    left_hash = data[-2 * NODE_HASH_SIZE: -1 * NODE_HASH_SIZE]
    right_hash = data[-1 * NODE_HASH_SIZE:]
    return (left_hash, right_hash)

def binary_expansion(x: bytes) -> str:
    return "".join([f"{bin(k).lstrip('0b').zfill(8)}" for k in x])

# export const binaryStringToBuffer = (str: string) => {
#     const byteSize = Math.ceil(str.length / 8);
#     const buf = Buffer.alloc(byteSize);

#     for (let i = 1; i <= byteSize; i += 1) {
#         buf.writeUInt8(
#             parseInt(str.substring(str.length - i * 8, str.length - i * 8 + 8), 2),
#             byteSize - i,
#         );
#     }
#     return buf;
# };