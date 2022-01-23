import dingus.tree.sparse_merkle_tree as smt
from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import os


def test_update_fixtures():
    with open("tests/tree/fixtures/smt.json", "r") as f:
        test_cases = json.load(f)["testCases"]
        for case in test_cases:
            asyncio.run(update_test(case))

async def update_test(case):
    keys = [bytes.fromhex(i) for i in case["input"]["keys"]]
    values = [bytes.fromhex(i) for i in case["input"]["values"]]
    _output = bytes.fromhex(case["output"]["merkleRoot"])

    _smt = smt.SparseMerkleTree()
    if keys:
        assert _smt.key_length == len(keys[0])
    assert _smt.root.hash == EMPTY_HASH

    for k, v in zip(keys, values):
        new_root = await _smt.update(k, v)
        assert _smt.root.hash == new_root.hash

    assert _smt.root.hash == _output

def test_batch_update_fixtures():
    with open("tests/tree/fixtures/smt.json", "r") as f:
        test_cases = json.load(f)["testCases"]
        for case in test_cases:
            asyncio.run(batch_test(case))

async def batch_test(case):
    keys = [bytes.fromhex(i) for i in case["input"]["keys"]]
    values = [bytes.fromhex(i) for i in case["input"]["values"]]
    _output = bytes.fromhex(case["output"]["merkleRoot"])

    _smt = smt.SparseMerkleTree()

    assert _smt.root.hash == EMPTY_HASH
    data = list(zip(keys, values))
    new_root = await _smt.update_batch(data, strict = True)
    print(new_root)
    assert _smt.root.hash == _output == new_root.hash