from dingus.tree.constants import (
    BRANCH_PREFIX,
    EMPTY_HASH_PLACEHOLDER_PREFIX,
    LEAF_PREFIX,
    DEFAULT_SUBTREE_NODES,
    DEFAULT_SUBTREE_MAX_HEIGHT,
)
from dingus.tree.types import SubTree
import dingus.tree.hasher as hasher
import os


def test_nodes():
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
        (0, 2**DEFAULT_SUBTREE_MAX_HEIGHT),
    ]
    st = SubTree(structure, nodes, hasher.TreeHasher())
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
        (0, 1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1)),
        (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1), 2**DEFAULT_SUBTREE_MAX_HEIGHT),
    ]
    st = SubTree(structure, nodes, hasher.TreeHasher())
    assert st.hash

    nodes_max_idx = b"\x01"
    structure_data = b"\x01\x01"
    nodes_data = LEAF_PREFIX + os.urandom(64) + EMPTY_HASH_PLACEHOLDER_PREFIX
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(structure) == len(nodes) == 2
    assert SubTree.structure_to_bins(structure) == [
        (0, 1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1)),
        (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1), 2**DEFAULT_SUBTREE_MAX_HEIGHT),
    ]
    st = SubTree(structure, nodes, hasher.TreeHasher())
    assert st.hash

    nodes_max_idx = b"\x01"
    structure_data = b"\x01\x01"
    nodes_data = EMPTY_HASH_PLACEHOLDER_PREFIX + LEAF_PREFIX + os.urandom(64)
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [1, 1]
    assert len(structure) == len(nodes) == 2
    assert SubTree.structure_to_bins(structure) == [
        (0, 1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1)),
        (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1), 2**DEFAULT_SUBTREE_MAX_HEIGHT),
    ]
    st = SubTree(structure, nodes, hasher.TreeHasher())
    assert st.hash

    r"""
        O
      /   \
     O     O
          / \
         O   O
    """
    # nodes_max_idx = b"\x02"
    # structure_data = b"\x01\x02\x02"
    # nodes_data = (
    #     EMPTY_HASH_PLACEHOLDER_PREFIX
    #     + LEAF_PREFIX
    #     + os.urandom(64)
    #     + BRANCH_PREFIX
    #     + os.urandom(32)
    # )
    data = b"\x02\x01\x02\x02\x02\x00Ir\r\xb7z\\\xa8Sq4\x93\xd4\xe1\x19&\xb4\x17\xaf\x0c\xaetj0ZR\xf5Us\x8e\xedG\xca\xd5\x8cx\t\xf5\xcfA\x19\xcc\x0f%\xc2$\xf7\x12M\x15\xb5\xd6+\xa9;\xc3\xd9H\xdb2\x87\x10&\xf0h\x01\x8d\xfe}\xfa\x8f\xb4\xa5\xa2h\x16\x868\xc8\xcc\xe0\xe2o\x87\xa2'2\n\xeei\x1f\x88r\xedj:\xba\x0e"

    structure, nodes = SubTree.parse(data)
    assert structure == [1, 2, 2]
    assert len(structure) == len(nodes) == 3
    assert SubTree.structure_to_bins(structure) == [
        (0, 1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1)),
        (
            1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1),
            (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1))
            + (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 2)),
        ),
        (
            (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 1))
            + (1 << (DEFAULT_SUBTREE_MAX_HEIGHT - 2)),
            2**DEFAULT_SUBTREE_MAX_HEIGHT,
        ),
    ]
    st = SubTree(structure, nodes, hasher.TreeHasher())

    print(data.hex())
    print(st.hash.hex())
    print(structure)
    assert (
        st.hash
        == b'\xc0\xfc\xf4\xb2W\x16"\x90]\xde\x08\x84\xefV\xd4\x94\xad4\x81\xd2\x8f\xa1gFo\x97\x0f,c>)%'
    )

    r"""
        O
      /   \
     O     O
    / \   / \
   O   O O   O
    """
    nodes_max_idx = (DEFAULT_SUBTREE_NODES - 1).to_bytes(1, "big")
    structure_data = (
        DEFAULT_SUBTREE_MAX_HEIGHT.to_bytes(1, "big") * DEFAULT_SUBTREE_NODES
    )
    nodes_data = b"".join(
        [BRANCH_PREFIX + os.urandom(32) for _ in range(DEFAULT_SUBTREE_NODES)]
    )
    data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [DEFAULT_SUBTREE_MAX_HEIGHT] * DEFAULT_SUBTREE_NODES
    print(len(structure))
    assert len(structure) == len(nodes) == DEFAULT_SUBTREE_NODES
    assert SubTree.structure_to_bins(structure) == [
        (i, (i + 1)) for i in range(DEFAULT_SUBTREE_NODES)
    ]
    st = SubTree(structure, nodes, hasher.TreeHasher())
    print(data.hex())
    print(st.hash.hex())
    print(structure)
    # assert st.hash == 0

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
    # nodes_max_idx = b"\x05"
    # structure_data = b"\x03\x03\x02\x02\x03\x03"
    data = b'\x05\x03\x03\x02\x02\x03\x03\x00\x1f\x93\x0fOf\x978\xb0&@j\x87,$\xdb)#\x871\x86\x89W\xae\x1d\xe0\xe5\xa6\x8b\xb0\xcf}\xa63\xe5\x08S:\x13\xda\x9c3\xfcd\xebx\xb1\x8b\xd0dl\x82\xd61f\x97\xde\xce\n\xeeZ:\x92\xe4W\x00\x08.j\xf1za\x85-\x01\xdf\xc1\x8e\x85\x9c \xb0\xb9tG+\xf6\x16\x92\x95\xc3l\xe18\x0c%P\xe1l\x16\xba\xbf\xe7\xd3 Oa\x85-\x10\x0fU2v\xad\x15I!\x98\x8d\xe3yv"\t\x1f\x05\x81\x88K\x00\x8bdy\x96\x84\x9bp\x88\x9d*8-\x8f\xa2\xf4$\x05\xc3\xbc\xa5q\x89\xde\x0b\xe5,\x92\xbb\xc0?\x0c\xd2\x11\x94\xdd\xd7v\xcf8z\x81\xd0\x11{b\x88\xe6\xa7$\xec\x14\xa5\x8c\xdd\xe3\xc1\x96)!\x91\xda6\r\xa8\x00\xecf\xadKHAS\xde\x04\x08i\xf8\x83:0\xa8\xfc\xdeO\xdf\x8f\xcb\xd7\x8d3\xc2\xfb!\x82\xdd\x8f\xfa;1\x1d:r\xa9\xae\xc8V\x0cV\xc6\x8dfZ\xd5LVD\xd4\x0e\xa4\xfc~\xd9\x14\xd4\xee\xa5\xda<\x04\x00\xe9;\xd7\x8c\xe1PA V\xa9\x07l\xf5\x89w\xff\x1ai{\x192\xab\xddR\xd7\xb9x\xfc\xe6\x91\x86\xd3\xa9\xcbrt\xec\xea\xc6\xb0\x80|\xe4\xdb\x07c\xdcYl\xd0\x0eY\x17qr\xdek]\xd1Y;3\xa7\x85\x00\xc8\xc4g0S\xda%\x99\x99\xcb\xc9P*\xefu\xc3\xc0\xb8K\xceB\xb1\xd1\xa2\xd47\xdf\x88\xd3+s{\xd3nzd\x10\x93\x9a\xc41\x91M\xe9G5?\x06\xbb\xbf\xc3\x1c\x86`\x9e\xc2\x91\xed\x9e\x13\xb6e\xf8j'
    # data = nodes_max_idx + structure_data + nodes_data
    structure, nodes = SubTree.parse(data)
    assert structure == [3, 3, 2, 2, 3, 3]
    assert len(structure) == len(nodes) == 6
    # The following is hard coded for DEFAULT_TREE_HEIGHT=4
    # assert SubTree.structure_to_bins(structure) == [
    #     (0, 2),
    #     (2, 4),
    #     (4, 8),
    #     (8, 12),
    #     (12, 14),
    #     (14, 16),
    # ]
    st = SubTree(structure, nodes, hasher.TreeHasher())

    _hash = b"z \x8d\xc2\xa2\x1c\xb8)\xe5\xfaM\xc7\xd8v\xbe\xf8\xe5-\xdd#\xae^\xa2L%g\xb2d\xbc\xd9\x1a#"

    assert st.hash == _hash

    print(data.hex())
    print(_hash.hex())
