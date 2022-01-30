from dingus.tree.utils import key_to_bin
from dingus.tree.constants import EMPTY_HASH_PLACEHOLDER, LEAF_PREFIX, DEFAULT_SUBTREE_NODES, DEFAULT_SUBTREE_HEIGHT
from dingus.tree.types import SubTree
import os

def test_nodes():
    nodes_len = b"\x01"
    structure_data = b"\x00"
    nodes_data = EMPTY_HASH_PLACEHOLDER
    data = nodes_len + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [0]
    assert len(nodes) == 1
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_len = b"\x02"
    structure_data = b"\x01\x01"
    nodes_data = LEAF_PREFIX + os.urandom(64) + LEAF_PREFIX + os.urandom(64)
    data = nodes_len + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(nodes) == 2
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_len = b"\x02"
    structure_data = b"\x01\x01"
    nodes_data = LEAF_PREFIX + os.urandom(64) + EMPTY_HASH_PLACEHOLDER
    data = nodes_len + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(nodes) == 2
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_len = b"\x02"
    structure_data = b"\x01\x01"
    nodes_data = EMPTY_HASH_PLACEHOLDER + LEAF_PREFIX + os.urandom(64)
    data = nodes_len + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(nodes) == 2
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_len = b"\x03"
    structure_data = b"\x01\x02\x02"
    nodes_data = EMPTY_HASH_PLACEHOLDER + LEAF_PREFIX + os.urandom(64) + LEAF_PREFIX + os.urandom(64)
    data = nodes_len + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 2, 2]
    assert len(nodes) == 3
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_len = DEFAULT_SUBTREE_NODES.to_bytes(1, "big")
    structure_data = (DEFAULT_SUBTREE_HEIGHT - 1).to_bytes(1, "big") * DEFAULT_SUBTREE_NODES
    nodes_data = b"".join([LEAF_PREFIX + os.urandom(64) for _ in range(DEFAULT_SUBTREE_NODES)])
    data = nodes_len + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [(DEFAULT_SUBTREE_HEIGHT - 1)] * DEFAULT_SUBTREE_NODES
    assert len(nodes) == DEFAULT_SUBTREE_NODES
    st = SubTree(structure, nodes)
    assert st.hash