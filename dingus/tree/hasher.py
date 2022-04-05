from ecpy.curves import Curve, Point

from dingus.utils import hash
from .constants import EMPTY_HASH, BRANCH_PREFIX
import dingus.tree.types as types

eddsa = Curve.get_curve('Ed25519')
ecc_generator  = Point(
    15112221349535400772501151409588531511454012693041857206046113283949847762202,
    46316835694926478169428394003475163141307993866256225615783033603165251855960,
    eddsa
)

class TreeHasher(object):
    empty = types.EmptyNode.hash

    @classmethod
    def hash(cls, nodes: list[types.TreeNode], structure: list[int]) -> bytes:
        assert len(nodes) == len(structure)
        if len(nodes) == 1:
            return nodes[0].hash

        hashes = [node.hash for node in nodes]

        structure = list(structure)
        for height in reversed(range(1, max(structure) + 1)):
            _hashes = []
            _structure = []

            i = 0
            while i < len(hashes):
                if structure[i] == height:
                    _hash = hash(BRANCH_PREFIX + hashes[i] + hashes[i + 1])
                    _hashes.append(_hash)
                    _structure.append(structure[i] - 1)
    
                    i += 1
                else:
                    _hashes.append(hashes[i])
                    _structure.append(structure[i])
                i += 1
            hashes = _hashes
            structure = _structure

        assert len(hashes) == 1
        return hashes[0]

class ECCHasher(object):
    empty = (int.from_bytes(EMPTY_HASH + b'\x00', "big")*ecc_generator).x.to_bytes(32, "big")

    @classmethod
    def hash(cls, nodes: list[types.TreeNode], structure: list[int]) -> bytes:
        if len(nodes) == 1:
            return (int.from_bytes(nodes[0].hash + structure[0].to_bytes(1, "big"), "big")*ecc_generator).x.to_bytes(32, "big")

        # mask = 0xFF* 32
        values = (nodes[i].hash + structure[i].to_bytes(1, "big") for i in range(len(nodes)))

        value = 1
        for v in values:
            value = (value*int.from_bytes(v, "big"))%eddsa.field
        
        value = int.from_bytes(hash(value.to_bytes(32, "big")), "big")
        return (ecc_generator).x.to_bytes(32, "big")

Hasher = TreeHasher | ECCHasher