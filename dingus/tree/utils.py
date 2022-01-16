from .constants import EMPTY_HASH
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