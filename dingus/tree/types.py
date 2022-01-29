from __future__ import annotations

from dataclasses import dataclass
from .errors import *
from dingus.utils import hash
from .constants import DEFAULT_KEY_LENGTH, LEAF_PREFIX, INTERNAL_LEAF_PREFIX, BRANCH_PREFIX, EMPTY_HASH, NODE_HASH_SIZE, DEFAULT_SUBTREE_HEIGHT

@dataclass
class LeafNode(object):
    key: bytes
    value: bytes

    @classmethod
    def parse(cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH) -> tuple[bytes, bytes]:
        key = data[len(LEAF_PREFIX):len(LEAF_PREFIX) + key_length]
        value = data[len(LEAF_PREFIX) + key_length:]
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
    def parse(cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH) -> tuple[bytes, bytes]:
        key = data[len(INTERNAL_LEAF_PREFIX):key_length + len(INTERNAL_LEAF_PREFIX)]
        value = data[key_length + len(INTERNAL_LEAF_PREFIX):]
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
        left_hash = data[-2 * NODE_HASH_SIZE: -1 * NODE_HASH_SIZE]
        right_hash = data[-1 * NODE_HASH_SIZE:]
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
    def parse_structure(cls, structure: bytes, subtree_height: int = DEFAULT_SUBTREE_HEIGHT) -> list[int]:
        assert len(structure) == 2**(subtree_height - 1)
        heights: list[int] = []
        for b in structure:
            # h = int.from_bytes(b, 'big')
            assert b <= subtree_height - 1
            heights.append(b)

        return heights

        # FIXME: this only works for subtree_height = 4, so i can use two bits to set an height in the range 0..3
        # A possible solution is to just use 1 byte per leaf for a total of subtree_nodes bytes and whatever
        # HEIGHT_BITS = 2
        # heights = []
        # bin_structure = f"{int.from_bytes(structure, 'big'):0{subtree_nodes*HEIGHT_BITS}b}"
        # print(structure, bin_structure, subtree_height)
        # idx = 0
        # while idx < len(bin_structure):
        #     heights.append(int(bin_structure[idx:idx + HEIGHT_BITS], 2))
        #     # only for subtree_height = 4
        #     idx += HEIGHT_BITS

        # return heights
        # int(s, 2).to_bytes(len(s) // 8

    @classmethod
    def parse(cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH, subtree_height: int = DEFAULT_SUBTREE_HEIGHT) -> list[TreeNode]:
        subtree_nodes = 2**(subtree_height - 1)
        structure_data, nodes_data = data[:subtree_nodes], data[subtree_nodes:]

        # Handle empty subtree case separately
        if structure_data.startswith(b"\x00"):
            assert structure_data == b"\x00" * subtree_nodes
            assert len(nodes_data) == 0
            root = EmptyNode()
            return ([0] * subtree_nodes, [root]* subtree_nodes)

        structure = cls.parse_structure(structure_data)
        
        nodes: list[TreeNode] = []
        leaf_data_length = len(LEAF_PREFIX) + key_length + NODE_HASH_SIZE
        branch_data_length = len(BRANCH_PREFIX) + NODE_HASH_SIZE + NODE_HASH_SIZE

        while len(nodes_data):
            if nodes_data.startswith(LEAF_PREFIX):
                key, value = LeafNode.parse(nodes_data[:leaf_data_length], key_length)
                node = LeafNode(key, value)
                nodes_data = nodes_data[leaf_data_length:]
            elif nodes_data.startswith(BRANCH_PREFIX):
                left_hash, right_hash = BranchNode.parse(nodes_data[:branch_data_length])
                node = BranchNode(left_hash, right_hash)
                nodes_data = nodes_data[branch_data_length:]
            else:
                raise InvalidDataError
            nodes.append(node)

        i = 0
        while i < len(structure):
            h = structure[i]
            nodes = nodes[:i] + [nodes[i]] * 2**(subtree_height - 1 - h) + nodes[i+1:]
            i += subtree_nodes >> h

        return (structure, nodes)

    @property
    def data(self) -> bytes:
        structure_data = b"".join([s.to_bytes("big") for s in self.structure])
        unique_node_data = dict.fromkeys([node.data for node in self.nodes]).keys()
        nodes_data = b"".join(unique_node_data)
        return structure_data + nodes_data

    @property
    def hash(self, subtree_height: int = DEFAULT_SUBTREE_HEIGHT) -> bytes:
        if not self.nodes:
            return EmptyNode.hash

        hashes = [node.hash for node in self.nodes]
        
        structure = list(self.structure)
        for height in reversed(range(1, subtree_height)):
            _hashes = []
            _structure = []
            for h, s in zip(hashes, structure):
                print(f"HEIGHT:{height} h:{s} hash:{h.hex()[:4]}")
            for i in range(0, len(hashes), 2):
                if structure[i] == height:
                    
                    _hash = hash(BRANCH_PREFIX + hashes[i] + hashes[i+1])
                    _hashes.append(_hash)
                    _structure.append(structure[i] - 1)
                    print(f"hashing:{hashes[i].hex()[:4]}+{hashes[i+1].hex()[:4]} hash:{_hash.hex()[:4]}")
                    # i += 1
                else:
                    _hashes.append(hashes[i])
                    _structure.append(structure[i])
            hashes = list(_hashes)
            structure = list(_structure)
            print()

        assert len(hashes) == 1
        return hashes[0]