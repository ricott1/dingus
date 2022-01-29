from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.constants import EMPTY_HASH, LEAF_PREFIX, DEFAULT_SUBTREE_NODES
from dingus.tree.types import SubTree
import asyncio
import os

def test_structure():
    structure_data = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert SubTree.parse_structure(structure_data) == [0] * DEFAULT_SUBTREE_NODES

    structure_data = b"\x00\x01\x00\x00\x00\x00\x00\x00"
    result = [0] * DEFAULT_SUBTREE_NODES
    result[1] = 1
    structure = SubTree.parse_structure(structure_data)
    assert structure == result
    st = SubTree(structure, [])
    assert st.hash == EMPTY_HASH

    structure_data = b"\x03\x00\x00\x00\x00\x00\x00\x00"
    result = [0] * DEFAULT_SUBTREE_NODES
    result[0] = 3

    assert SubTree.parse_structure(structure_data) == result

def test_nodes():
    structure_data = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    nodes_data = b""
    data = structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [0] * DEFAULT_SUBTREE_NODES
    assert len(nodes) == DEFAULT_SUBTREE_NODES

    structure_data = b"\x03\x03\x03\x03\x03\x03\x03\x03"
    nodes_data = b""
    for _ in range(DEFAULT_SUBTREE_NODES):
        nodes_data += LEAF_PREFIX + os.urandom(64)
    data = structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [3] * DEFAULT_SUBTREE_NODES
    assert len(nodes) == DEFAULT_SUBTREE_NODES

    structure_data = b"\x02\x02\x03\x03\x03\x03\x03\x03"
    nodes_data = b""
    for _ in range(DEFAULT_SUBTREE_NODES - 1):
        nodes_data += LEAF_PREFIX + os.urandom(64)
    data = structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [2, 2, 3, 3, 3, 3, 3, 3]
    assert len(nodes) == DEFAULT_SUBTREE_NODES
    assert nodes[0] == nodes[1]
    st = SubTree(structure, nodes)
    assert st.hash 

    structure_data = b"\x02\x02\x03\x03\x01\x01\x01\x01"
    nodes_data = b""
    for _ in range(4):
        nodes_data += LEAF_PREFIX + os.urandom(64)
    data = structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [2, 2, 3, 3, 1, 1, 1, 1]
    assert len(nodes) == DEFAULT_SUBTREE_NODES
    assert nodes[0] == nodes[1]
    st = SubTree(structure, nodes)
    assert st.hash