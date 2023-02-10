from dingus.tree.constants import EMPTY_HASH, LEAF_PREFIX, BRANCH_PREFIX
from dingus.crypto import hash
import math


class MerkleTree(object):
    def __init__(self, data: list[bytes] = []) -> None:
        self.root = EMPTY_HASH
        self.size = 0
        self.append_path = [self.root]
        self.append(data)

    @classmethod
    def leaf_hash(cls, data: bytes) -> bytes:
        return hash(LEAF_PREFIX + data)

    @classmethod
    def branch_hash(cls, data: bytes) -> bytes:
        return hash(BRANCH_PREFIX + data)

    @classmethod
    def merkle_root(cls, data: list[bytes]) -> bytes:
        """Returns the Merkle root from a list of bytes as specified 
        in https://github.com/LiskHQ/lips/blob/main/proposals/lip-0031.md#merkle-root
        """

        size = len(data)
        if size == 0:
            return EMPTY_HASH
        if size == 1:
            return MerkleTree.leaf_hash(data[0])

        # Largest power of two smaller than size
        k = 2 ** (math.floor(math.log2(size - 1)))
        # Split the data array into 2 subtrees. leftTree from index 0 to index k (not included), rightTree for the rest
        left_tree = data[:k]
        right_tree = data[k:]
        return MerkleTree.branch_hash(MerkleTree.merkle_root(left_tree) + MerkleTree.merkle_root(right_tree))

    def append(self, data: list[bytes]) -> bytes:
        """
        Append new values to the tree.
        """

        for value in data:
            self._append(value)

        return self.root

    def _append(self, data: bytes) -> bytes:
        """
        Append a new value to the tree.
        """

        h = MerkleTree.leaf_hash(data)
        if self.size == 0:
            self.root = h
            self.append_path = [h]
            self.size += 1
            return h

        spliced = False
        for i in range(math.floor(math.log2(self.size)) + 1):
            if ((self.size >> i) & 1) == 1:
                h = MerkleTree.branch_hash(self.append_path.pop(0) + h)
            elif not spliced:
                new_append_path = [h] + self.append_path
                spliced = True
        if not spliced:
            new_append_path = [h]

        self.root = h
        self.append_path = new_append_path
        self.size += 1
        return self.root

    @classmethod
    def get_right_witness(cls, size: int, data: list[bytes]) -> list[bytes]:
        """
        Calculate right witness for input data.
        """

        assert size > 0

        if len(data) == 0:
            return []

        data = [MerkleTree.leaf_hash(d) for d in data]
        witness = []
        # incrementalIdx is initially equal to idx and it is later increased to signal that a subtree has been completed
        incremental_idx = size
        height = math.ceil(math.log2(size + len(data))) + 1

        for l in range(height):

            if len(data) == 0:
                break

            # d is the l-th binary digit of idx (from the right)
            d = (incremental_idx >> l) & 1
            if d == 1:
                witness.append(data.pop(0))
                # Complete the subtree after right hashing
                incremental_idx += 1 << l

            # hash pairs of nodes from the right
            _data = []
            for i in range(0, len(data), 2):
                if i + 1 < len(data):
                    _data.append(MerkleTree.branch_hash(data[i] + data[i + 1]))
                else:
                    _data.append(data[i])
            data = _data

        return witness

    @classmethod
    def root_from_append_path(cls, append_path: list[bytes]) -> bytes:
        """
        Calculate root from append path.
        """

        if len(append_path) == 0:
            return EMPTY_HASH

        h = append_path.pop(0)
        while len(append_path) > 0:
            g = append_path.pop(0)
            h = MerkleTree.branch_hash(g + h)

        return h

    @classmethod
    def root_from_right_witness(cls, size: int, append_path: list[bytes], right_witness: list[bytes]) -> bytes:
        """
        Calculate root from right witness.
        """

        if len(append_path) == 0:
            return MerkleTree.root_from_append_path(right_witness)

        if len(right_witness) == 0:
            return MerkleTree.root_from_append_path(append_path)

        l = 0
        incremental_idx = size
        h = b""
        while len(append_path) > 0 or len(right_witness) > 0:
            d = (size >> l) & 1
            if len(append_path) > 0 and d == 1:
                left_hash = append_path.pop(0)
                if not h:
                    right_hash = right_witness.pop(0)
                    h = MerkleTree.branch_hash(left_hash + right_hash)
                    incremental_idx += 1 << l
                else:
                    h = MerkleTree.branch_hash(left_hash + h)

            r = (incremental_idx >> l) & 1
            if len(right_witness) > 0 and r == 1:
                right_hash = right_witness.pop(0)
                h = MerkleTree.branch_hash(h + right_hash)
                incremental_idx += 1 << l

            l += 1

        return h
