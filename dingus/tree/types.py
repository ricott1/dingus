from __future__ import annotations

from dataclasses import dataclass

from .errors import *
from dingus.utils import hash
from .constants import (
    DEFAULT_KEY_LENGTH,
    LEAF_PREFIX,
    INTERNAL_LEAF_PREFIX,
    BRANCH_PREFIX,
    EMPTY_HASH,
    NODE_HASH_SIZE,
    DEFAULT_SUBTREE_MAX_HEIGHT,
    EMPTY_HASH_PLACEHOLDER_PREFIX,
)

import dingus.tree.hasher as hasher


@dataclass
class LeafNode(object):
    key: bytes
    value: bytes

    @classmethod
    def parse(
        cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH
    ) -> tuple[bytes, bytes]:
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
class InternalLeafNode(object):
    key: bytes
    value: bytes

    @classmethod
    def parse(
        cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH
    ) -> tuple[bytes, bytes]:
        key = data[len(INTERNAL_LEAF_PREFIX) : key_length + len(INTERNAL_LEAF_PREFIX)]
        value = data[key_length + len(INTERNAL_LEAF_PREFIX) :]
        return (key, value)

    @property
    def data(self) -> bytes:
        return INTERNAL_LEAF_PREFIX + self.key + self.value

    @property
    def hash(self) -> bytes:
        return hash(self.value)


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
    def structure_to_bins(
        cls, structure: list[int], subtree_height: int = DEFAULT_SUBTREE_MAX_HEIGHT
    ) -> list[tuple[int, int]]:
        V = 0
        bins = []
        
        for h in structure:
            bins.append((V, V + (1 <<(subtree_height - h))))
            V += (1 <<(subtree_height - h))

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
                _hash = StubNode.parse(
                    nodes_data[:subtree_branch_data_length]
                )
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
