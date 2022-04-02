from dingus.tree.hasher import TreeHasher, ECCHasher
from dingus.tree.types import LeafNode
import os
import random

def test_tree_hasher():
    n = 256
    nodes = [LeafNode(os.urandom(32), os.urandom(32)) for _ in range(n)]
    structure = [8 for _ in range(n)]
    for _ in range(100):
        TreeHasher.hash(nodes, structure)

def test_ecc_hasher():
    n = 256
    nodes = [LeafNode(os.urandom(32), os.urandom(32)) for _ in range(n)]
    structure = [8 for _ in range(n)]
    values = [int.from_bytes(nodes[i].hash[:16] + structure[i].to_bytes(1, "big"), "big") for i in range(len(nodes))]
    for _ in range(100):
        ECCHasher.fast_hash(values)
    

def test_ecc_hasher_safe():
    from ecpy.curves import Curve,Point

    cv = Curve.get_curve('Ed25519')

    base  = Point(15112221349535400772501151409588531511454012693041857206046113283949847762202,
            46316835694926478169428394003475163141307993866256225615783033603165251855960,
            cv)

    n = 256
    proof_idx = random.randint(0, n-1)
    nodes = [os.urandom(32) for _ in range(n)]
    structure = [bytes.fromhex("08") for _ in range(n)]

    values = [int.from_bytes(nodes[i] + structure[i], "big") for i in range(n)]
    value = 1
    witness = 1
    point = base

    for i, v in enumerate(values):
        value *= v
        point *= v
        if i != proof_idx:
            witness *= v

    assert (witness*values[proof_idx])*base == value*base == point

