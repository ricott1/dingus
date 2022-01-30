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
    DEFAULT_SUBTREE_HEIGHT,
    EMPTY_HASH_PLACEHOLDER,
)


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

    @property
    def data(self) -> bytes:
        return BRANCH_PREFIX + self.left_hash + self.right_hash

    @property
    def hash(self) -> bytes:
        return hash(self.data)


@dataclass
class EmptyNode(object):
    hash = EMPTY_HASH


TreeNode = LeafNode | BranchNode | EmptyNode | InternalLeafNode


@dataclass
class SubTree(object):
    structure: list[int]
    nodes: list[TreeNode]

    @classmethod
    def parse(
        cls,
        data: bytes,
        key_length: int = DEFAULT_KEY_LENGTH,
        subtree_height: int = DEFAULT_SUBTREE_HEIGHT,
    ) -> list[TreeNode]:
        subtree_nodes = data[0]
        # Handle empty subtree case separately
        if subtree_nodes == 0:
            return ([0], [EmptyNode()])

        assert 1 <= subtree_nodes <= 2 ** (subtree_height - 1)
        structure_data, nodes_data = (
            data[1 : subtree_nodes + 1],
            data[subtree_nodes + 1 :],
        )

        structure = [h for h in structure_data]

        nodes: list[TreeNode] = []
        leaf_data_length = len(LEAF_PREFIX) + key_length + NODE_HASH_SIZE
        branch_data_length = len(BRANCH_PREFIX) + NODE_HASH_SIZE + NODE_HASH_SIZE

        while len(nodes_data):
            if nodes_data.startswith(LEAF_PREFIX):
                key, value = LeafNode.parse(nodes_data[:leaf_data_length], key_length)
                node = LeafNode(key, value)
                nodes_data = nodes_data[leaf_data_length:]
            elif nodes_data.startswith(BRANCH_PREFIX):
                left_hash, right_hash = BranchNode.parse(
                    nodes_data[:branch_data_length]
                )
                node = BranchNode(left_hash, right_hash)
                nodes_data = nodes_data[branch_data_length:]
            elif nodes_data.startswith(EMPTY_HASH_PLACEHOLDER):
                node = EmptyNode()
                nodes_data = nodes_data[len(EMPTY_HASH_PLACEHOLDER) :]
            else:
                raise InvalidDataError
            nodes.append(node)

        return (structure, nodes)

    @property
    def data(self) -> bytes:
        nodes_len = len(self.structure).to_bytes(1, "big")
        structure_data = b"".join([s.to_bytes(1, "big") for s in self.structure])
        nodes_data = b"".join([node.data for node in self.nodes])
        return nodes_len + structure_data + nodes_data

    @property
    def hash(self, subtree_height: int = DEFAULT_SUBTREE_HEIGHT) -> bytes:

        hashes = [node.hash for node in self.nodes]
        print(f"HASHES {[h.hex()[:4] for h in hashes]}")
        print(f"Structure {self.structure}")
        structure = list(self.structure)
        for height in reversed(range(1, subtree_height)):
            _hashes = []
            _structure = []
            for h, s in zip(hashes, structure):
                print(f"HEIGHT:{height} h:{s} hash:{h.hex()[:4]}")

            i = 0
            while i < len(hashes):
                if structure[i] == height:
                    _hash = hash(BRANCH_PREFIX + hashes[i] + hashes[i + 1])
                    _hashes.append(_hash)
                    _structure.append(structure[i] - 1)
                    print(
                        f"hashing:{hashes[i].hex()[:4]}+{hashes[i+1].hex()[:4]} hash:{_hash.hex()[:4]}"
                    )
                    i += 1
                else:
                    _hashes.append(hashes[i])
                    _structure.append(structure[i])
                i += 1
            hashes = list(_hashes)
            structure = list(_structure)
            print()

        assert len(hashes) == 1
        return hashes[0]
