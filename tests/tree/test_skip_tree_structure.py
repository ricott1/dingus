from dingus.tree.constants import (
    BRANCH_PREFIX,
    EMPTY_HASH_PLACEHOLDER_PREFIX,
    LEAF_PREFIX,
    DEFAULT_SUBTREE_NODES,
    DEFAULT_SUBTREE_HEIGHT,
)
from dingus.tree.types import SubTree
import os
import time

def test_hashing(capsys):
    start_time = time.time()
    data = [os.urandom(1500) for _ in range(20000)]
    with capsys.disabled():
        print(f"\ndata: {time.time() - start_time:.2f}s")

    for d in data:
        hash(d)
    with capsys.disabled():
        print(f"\nhashing: {time.time() - start_time:.2f}s")

def test_nodes():
    return
    r"""
    O
    """
    nodes_max_idx = b"\x00"
    structure_data = b"\x00"
    nodes_data = EMPTY_HASH_PLACEHOLDER_PREFIX
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [0]
    assert len(structure) == len(nodes) == 1
    assert SubTree.structure_to_bins(structure) == [
        (0, 2<<DEFAULT_SUBTREE_HEIGHT),
    ]
    st = SubTree(structure, nodes)
    assert st.hash

    r"""
        O
      /   \
     O     O
    """
    nodes_max_idx = b"\x01"
    structure_data = b"\x01\x01"
    nodes_data = LEAF_PREFIX + os.urandom(64) + LEAF_PREFIX + os.urandom(64)
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(structure) == len(nodes) == 2
    assert SubTree.structure_to_bins(structure) == [
        (0, 2 << (DEFAULT_SUBTREE_HEIGHT - 1)),
        (2 << (DEFAULT_SUBTREE_HEIGHT - 1), 2<<DEFAULT_SUBTREE_HEIGHT),
    ]
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_max_idx = b"\x01"
    structure_data = b"\x01\x01"
    nodes_data = LEAF_PREFIX + os.urandom(64) + EMPTY_HASH_PLACEHOLDER_PREFIX
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(structure) == len(nodes) == 2
    assert SubTree.structure_to_bins(structure) == [
        (0, 2 << (DEFAULT_SUBTREE_HEIGHT - 1)),
        (2 << (DEFAULT_SUBTREE_HEIGHT - 1), 2<<DEFAULT_SUBTREE_HEIGHT),
    ]
    st = SubTree(structure, nodes)
    assert st.hash

    nodes_max_idx = b"\x01"
    structure_data = b"\x01\x01"
    nodes_data = EMPTY_HASH_PLACEHOLDER_PREFIX + LEAF_PREFIX + os.urandom(64)
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(structure) == len(nodes) == 2
    assert SubTree.structure_to_bins(structure) == [
        (0, 2 << (DEFAULT_SUBTREE_HEIGHT - 1)),
        (2 << (DEFAULT_SUBTREE_HEIGHT - 1), 2<<DEFAULT_SUBTREE_HEIGHT),
    ]
    st = SubTree(structure, nodes)
    assert st.hash

    r"""
        O
      /   \
     O     O
          / \
         O   O
    """
    nodes_max_idx = b"\x02"
    structure_data = b"\x01\x02\x02"
    nodes_data = (
        EMPTY_HASH_PLACEHOLDER_PREFIX
        + LEAF_PREFIX
        + os.urandom(64)
        + LEAF_PREFIX
        + os.urandom(32)
    )
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 2, 2]
    assert len(structure) == len(nodes) == 3
    assert SubTree.structure_to_bins(structure) == [
        (0, 2 << (DEFAULT_SUBTREE_HEIGHT - 1)),
        (
            2 << (DEFAULT_SUBTREE_HEIGHT - 1),
            (2 << (DEFAULT_SUBTREE_HEIGHT - 1)) + (2 << (DEFAULT_SUBTREE_HEIGHT - 2)),
        ),
        (
            (2 << (DEFAULT_SUBTREE_HEIGHT - 1)) + (2 << (DEFAULT_SUBTREE_HEIGHT - 2)),
            2<<DEFAULT_SUBTREE_HEIGHT,
        ),
    ]
    st = SubTree(structure, nodes)
    assert st.hash

    r"""
        O
      /   \
     O     O
    / \   / \
   O   O O   O
    """
    nodes_max_idx = (DEFAULT_SUBTREE_NODES - 1).to_bytes(1, "big")
    structure_data = (DEFAULT_SUBTREE_HEIGHT - 1).to_bytes(1, "big") * DEFAULT_SUBTREE_NODES
    nodes_data = b"".join(
        [BRANCH_PREFIX + os.urandom(64) for _ in range(DEFAULT_SUBTREE_NODES)]
    )
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [DEFAULT_SUBTREE_HEIGHT - 1] * DEFAULT_SUBTREE_NODES
    assert len(structure) == len(nodes) == DEFAULT_SUBTREE_NODES
    assert SubTree.structure_to_bins(structure) == [
        (i, (i + 1)) for i in range(DEFAULT_SUBTREE_NODES)
    ]
    st = SubTree(structure, nodes)
    assert st.hash

    r"""
            O
          /   \
         /     \
        O       O
       / \     / \
      /   \   /   \
     O     O O     O
    / \           / \
   O   O         O   O
    """
    nodes_max_idx = b"\x05"
    structure_data = b"\x03\x03\x02\x02\x03\x03"
    nodes_data = b"".join([LEAF_PREFIX + os.urandom(64) for _ in range(6)])
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [3, 3, 2, 2, 3, 3]
    assert len(structure) == len(nodes) == 6
    # The following is hard coded for DEFAULT_TREE_HEIGHT=8
    assert SubTree.structure_to_bins(structure) == [
        (0, 32),
        (32, 64),
        (64, 128),
        (128, 192),
        (192, 224),
        (224, 256),
    ]
    st = SubTree(structure, nodes)
    assert st.hash
