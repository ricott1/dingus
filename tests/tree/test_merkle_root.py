from dingus.tree.merkle_tree import MerkleTree
from dingus.tree.utils import merkle_root
from dingus.tree.constants import EMPTY_HASH
from dingus.crypto import hash
import json


def test_empty_tree():
    assert merkle_root([]) == EMPTY_HASH


def test_fixtures():
    with open("./fixtures/rmt.json", "r") as f:
        test_cases = json.load(f)["testCases"]

    for case in test_cases:
        _input = [bytes.fromhex(i) for i in case["input"]["values"]]
        _output = bytes.fromhex(case["output"]["merkleRoot"])
        mt = MerkleTree(_input)
        assert _output == MerkleTree.merkle_root(_input)
        assert _output == mt.root

def test_right_witness():
    data = [hash(int.to_bytes(i, 4, "big")) for i in range(100)]
    for a in range(1, 50):
        for b in range(a + 1, 100): 
            mt = MerkleTree(data[:a])
            mt2 = MerkleTree(data[:b])
            right_witness = MerkleTree.get_right_witness(mt.size, data[a:b])
            wit_root = MerkleTree.root_from_right_witness(mt.size, mt.append_path, right_witness)
            assert mt2.root == wit_root

def test_right_witness_from_fixtures():
    with open("./fixtures/rmt.json", "r") as f:
        test_cases = json.load(f)["testCases"]

    for case in test_cases:
        _input = [bytes.fromhex(i) for i in case["input"]["values"]]
        _output = bytes.fromhex(case["output"]["merkleRoot"])
        mt = MerkleTree(_input)
        for n in range(1, len(_input) + 1):
            partial_mt = MerkleTree(_input[:n])
            right_witness = MerkleTree.get_right_witness(partial_mt.size, _input[n:])
            wit_root = MerkleTree.root_from_right_witness(partial_mt.size, partial_mt.append_path, right_witness)
            assert wit_root == mt.root == _output

def test_bin_stuff():
    for n in range(27):
        a = bin(n)[2:]
        print(f"n: {n}, a: {a}")
        for i in range(len(a)):
            print(i, a[len(a) - 1 - i], (n & (1 << i)) >> i)
            assert ((n & (1 << i)) >> i) == int(a[len(a) - 1 - i])


if __name__ == "__main__":
    test_fixtures()
    test_right_witness()
    test_right_witness_from_fixtures()