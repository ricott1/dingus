from __future__ import annotations

from dataclasses import dataclass
import dingus.tree.hasher as hasher
from dingus.tree.errors import *
from dingus.crypto import hash
from dingus.tree.constants import (
    DEFAULT_KEY_LENGTH,
    EMPTY_VALUE,
    LEAF_PREFIX,
    BRANCH_PREFIX,
    EMPTY_HASH,
    NODE_HASH_SIZE,
    DEFAULT_SUBTREE_MAX_HEIGHT,
    EMPTY_HASH_PLACEHOLDER_PREFIX,
)
from dingus.tree.utils import binary_expansion


@dataclass
class LeafNode(object):
    key: bytes
    value: bytes

    @classmethod
    def parse(cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH) -> tuple[bytes, bytes]:
        key = data[len(LEAF_PREFIX) : len(LEAF_PREFIX) + key_length]
        value = data[len(LEAF_PREFIX) + key_length :]
        return (key, value)

    @classmethod
    def _hash(cls, data: bytes) -> bytes:
        return hash(LEAF_PREFIX + data)

    @classmethod
    def from_data(cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH) -> LeafNode:
        assert len(data) == len(LEAF_PREFIX) + key_length + NODE_HASH_SIZE
        key, value = cls.parse(data, key_length)
        return LeafNode(key, value)

    @property
    def data(self) -> bytes:
        return LEAF_PREFIX + self.key + self.value

    @property
    def hash(self) -> bytes:
        return hash(self.data)


@dataclass
class BranchNode(object):
    left_hash: bytes
    right_hash: bytes

    @classmethod
    def parse(cls, data: bytes) -> tuple[bytes, bytes]:
        left_hash = data[-2 * NODE_HASH_SIZE : -1 * NODE_HASH_SIZE]
        right_hash = data[-1 * NODE_HASH_SIZE :]
        return (left_hash, right_hash)

    @classmethod
    def from_data(cls, data: bytes) -> BranchNode:
        assert len(data) == len(BRANCH_PREFIX) + NODE_HASH_SIZE + NODE_HASH_SIZE
        left_hash, right_hash = cls.parse(data)
        return BranchNode(left_hash, right_hash)

    @classmethod
    def _hash(cls, data: bytes) -> bytes:
        return hash(BRANCH_PREFIX + data)

    @property
    def data(self) -> bytes:
        return BRANCH_PREFIX + self.left_hash + self.right_hash

    @property
    def hash(self) -> bytes:
        return hash(self.data)


@dataclass
class StubNode(object):
    hash: bytes

    @classmethod
    def parse(cls, data: bytes) -> bytes:
        return data[len(BRANCH_PREFIX) :]

    @classmethod
    def from_data(cls, data: bytes) -> StubNode:
        assert len(data) == len(BRANCH_PREFIX) + NODE_HASH_SIZE
        _hash = cls.parse(data)
        return StubNode(_hash)

    @property
    def data(self) -> bytes:
        return BRANCH_PREFIX + self.hash


@dataclass
class EmptyNode(object):
    hash = EMPTY_HASH

    @classmethod
    def from_data(cls, data: bytes) -> StubNode:
        assert len(data) == len(EMPTY_HASH_PLACEHOLDER_PREFIX)
        return EmptyNode()

    @property
    def data(self) -> bytes:
        return EMPTY_HASH_PLACEHOLDER_PREFIX


@dataclass
class SubTree(object):
    structure: list[int]
    nodes: list[TreeNode]
    hasher: hasher.Hasher

    @classmethod
    def structure_to_bins(cls, structure: list[int], subtree_height: int = DEFAULT_SUBTREE_MAX_HEIGHT) -> list[tuple[int, int]]:
        V = 0
        bins = []

        for h in structure:
            bins.append((V, V + (1 << (subtree_height - h))))
            V += 1 << (subtree_height - h)

        assert V == (1 << subtree_height)
        return bins

    @classmethod
    def parse(
        cls,
        data: bytes,
        key_length: int = DEFAULT_KEY_LENGTH,
    ) -> tuple[list[int], list[TreeNode]]:
        subtree_nodes = data[0] + 1
        # assert 1 <= subtree_nodes <= (2<<subtree_height)

        structure_data, nodes_data = (
            data[1 : subtree_nodes + 1],
            data[subtree_nodes + 1 :],
        )

        structure = [h for h in structure_data]

        nodes: list[TreeNode] = []
        leaf_data_length = len(LEAF_PREFIX) + key_length + NODE_HASH_SIZE
        subtree_branch_data_length = len(BRANCH_PREFIX) + NODE_HASH_SIZE

        while len(nodes_data):
            if nodes_data.startswith(LEAF_PREFIX):
                node = LeafNode.from_data(nodes_data[:leaf_data_length], key_length)
                nodes_data = nodes_data[leaf_data_length:]
            elif nodes_data.startswith(BRANCH_PREFIX):
                _hash = StubNode.parse(nodes_data[:subtree_branch_data_length])
                node = StubNode(_hash)
                nodes_data = nodes_data[subtree_branch_data_length:]
            elif nodes_data.startswith(EMPTY_HASH_PLACEHOLDER_PREFIX):
                node = EmptyNode()
                nodes_data = nodes_data[len(EMPTY_HASH_PLACEHOLDER_PREFIX) :]
            else:
                raise InvalidDataError
            nodes.append(node)

        # assert len(structure) == len(nodes) == subtree_nodes
        return (structure, nodes)

    @property
    def data(self) -> bytes:
        subtree_nodes = (len(self.structure) - 1).to_bytes(1, "big")
        structure_data = b"".join([s.to_bytes(1, "big") for s in self.structure])
        nodes_data = b"".join([node.data for node in self.nodes])
        return subtree_nodes + structure_data + nodes_data

    @property
    def hash(self) -> bytes:
        return self.hasher.hash(self.nodes, self.structure)


TreeNode = LeafNode | BranchNode | EmptyNode | StubNode


@dataclass
class Query(object):
    key: bytes
    value: bytes
    bitmap: bytes

    def __post_init__(self) -> None:
        self.binary_bitmap = binary_expansion(self.bitmap).lstrip("0")
        self.hash = EMPTY_HASH if self.value == EMPTY_VALUE else LeafNode(self.key, self.value).hash
    
    def __str__(self) -> str:
        return f"Query(key={self.key.hex()}, value={self.value.hex()}, bitmap={self.bitmap.hex()})"

    @property
    def binary_path(self) -> str:
        # Convert the key to binary
        return binary_expansion(self.key)[:self.height]

    @property
    def binary_key(self) -> str:
        # Convert the key to binary with fixed length
        return binary_expansion(self.key)

    @property
    def height(self) -> int:
        return len(self.binary_bitmap)

    def is_sibling_of(self, q: Query) -> bool:
        if len(self.binary_bitmap) != len(q.binary_bitmap):
            return False

        # end of string is exclusive
        if self.binary_key[: self.height - 1] != q.binary_key[: q.height - 1]:
            return False

        return self.binary_key[self.height - 1] != q.binary_key[self.height - 1]


@dataclass
class QueryWithProof(Query):
    ancestor_hashes: list[bytes]
    sibling_hashes: list[bytes]


@dataclass
class Proof(object):
    sibling_hashes: list[bytes]
    queries: list[Query]

    def __str__(self) -> str:
        keys = '\n      '.join([''] + [q.key.hex() for q in self.queries] + [''])
        sibling_hashes = '\n      '.join([''] + [h.hex() for h in self.sibling_hashes] + [''])
        return f"""
Proof:
    keys:{keys}
    sibling_hashes:{sibling_hashes}
"""

