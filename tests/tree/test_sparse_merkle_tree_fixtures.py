import dingus.tree.sparse_merkle_tree as smt
from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt

def get_cases() -> list[dict]:
    _cases = []
    with open("tests/tree/fixtures/smt.json", "r") as f:
        test_cases = json.load(f)["testCases"]
    for case in test_cases:
        _cases.append({
            "keys": [bytes.fromhex(i) for i in case["input"]["keys"]],
            "values": [bytes.fromhex(i) for i in case["input"]["values"]],
            "root": bytes.fromhex(case["output"]["merkleRoot"])
        })
    return _cases

test_cases = get_cases()

def test_update_fixtures():
    for case in test_cases:
        asyncio.run(update_test(case))


async def update_test(case):
    _smt = smt.SparseMerkleTree()
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    if keys:
        assert _smt.key_length == len(keys[0])
    assert _smt.root.hash == EMPTY_HASH

    for k, v in zip(keys, values):
        new_root = await _smt.update(k, v)
        assert _smt.root.hash == new_root.hash

    assert _smt.root.hash == root


def test_batch_update_fixtures(capsys):
    for case in test_cases:
        asyncio.run(batch_test(case, capsys))


async def batch_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]

    _smt = smt.SparseMerkleTree()

    assert _smt.root.hash == EMPTY_HASH
    data = list(zip(keys, values))
    new_root = await _smt.update_batch(data, strict=True)
    
    assert _smt.root.hash == root == new_root.hash
    # with capsys.disabled():
    #     print("\n BATCH TREE")
    #     print(await _smt.print(_smt.root))
    

def test_skip_merkle_tree_fixtures(capsys):
    for case in test_cases:
        asyncio.run(skip_test(case, capsys))


async def skip_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]

    _skmt = skmt.SkipMerkleTree()

    assert _skmt.root.hash == EMPTY_HASH
    data = list(zip(keys, values))
    new_root = await _skmt.update(data, strict=True)
    if not _skmt.root.hash == root == new_root.hash:
        with capsys.disabled():
            print("\n SKIP TREE")
            print(await _skmt.print(_skmt.root))

    assert _skmt.root.hash == root == new_root.hash
