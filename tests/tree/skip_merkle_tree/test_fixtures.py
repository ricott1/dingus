from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt
import dingus.tree.sparse_merkle_tree as smt


def get_cases() -> list[dict]:
    _cases = []
    with open("tests/tree/fixtures/smt.json", "r") as f:
        test_cases = json.load(f)["testCases"]
    for case in test_cases:
        _cases.append({
            "keys": [bytes.fromhex(i) for i in case["input"]["keys"]],
            "delete_keys": [bytes.fromhex(i) for i in case["input"]["deleteKeys"]],
            "values": [bytes.fromhex(i) for i in case["input"]["values"]],
            "root": bytes.fromhex(case["output"]["merkleRoot"])
        })

    return _cases

test_cases = get_cases()


def test_skip_merkle_tree_fixtures(capsys):
    for case in test_cases:
        asyncio.run(skip_test(case, capsys))


async def skip_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]

    _skmt = skmt.SkipMerkleTree()
    assert _skmt.root.hash == EMPTY_HASH
    print("CASE:", len(keys))
    new_root = await _skmt.update(keys, values)

    assert _skmt.root.hash == root == new_root.hash

    _smt = smt.SparseMerkleTree()
    assert _smt.root.hash == EMPTY_HASH
    print("CASE:", len(keys))
    smt_new_root = await _smt.update(keys, values)

    assert _smt.root.hash == root == smt_new_root.hash
