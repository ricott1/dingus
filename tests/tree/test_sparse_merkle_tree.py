from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.constants import EMPTY_HASH
from dingus.tree.utils import binary_expansion
import json
import asyncio
import os


def test_bytes_to_binary_string_length():
    for length in range(0, 48):
        assert len(binary_expansion(os.urandom(length))) == 8 * length

def test_bytes_to_binary_string():
    assert binary_expansion(bytes.fromhex("00")) == "00000000"
    assert binary_expansion(bytes.fromhex("01")) == "00000001"
    assert binary_expansion(bytes.fromhex("ff")) == "11111111"
    assert binary_expansion(bytes.fromhex("0000")) == "0000000000000000"
    assert binary_expansion(bytes.fromhex("0001")) == "0000000000000001"
    assert binary_expansion(bytes.fromhex("ffff")) == "1111111111111111"
    assert binary_expansion(bytes.fromhex("00ff")) == "0000000011111111"
    assert binary_expansion(bytes.fromhex("0000f0")) == "000000000000000011110000"
    assert binary_expansion(bytes.fromhex("001001")) == "000000000001000000000001"


def test_fixtures():
    with open("tests/tree/fixtures/smt.json", "r") as f:
        test_cases = json.load(f)["testCases"]
        for case in test_cases:
            asyncio.run(case_testing(case))

async def case_testing(case):
    keys = [bytes.fromhex(i) for i in case["input"]["keys"]]
    values = [bytes.fromhex(i) for i in case["input"]["values"]]
    _output = bytes.fromhex(case["output"]["merkleRoot"])

    smt = SparseMerkleTree()
    assert smt.root_hash == EMPTY_HASH

    for k, v in zip(keys, values):
        new_root = await smt.update(k, v)
        assert smt.root_hash == new_root.hash

    assert smt.root_hash == _output