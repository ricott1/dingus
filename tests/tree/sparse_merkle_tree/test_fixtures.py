import dingus.tree.sparse_merkle_tree as smt
from dingus.tree.constants import EMPTY_HASH
import json
import asyncio


def get_cases() -> list[dict]:
    _cases = []
    with open("tests/tree/fixtures/smt.json", "r") as f:
        test_cases = json.load(f)["testCases"]
    for case in test_cases:
        data = zip(
            [bytes.fromhex(i) for i in case["input"]["keys"]],
            [bytes.fromhex(i) for i in case["input"]["values"]],
        )
        sorted_data = sorted(data, key=lambda d: d[0])
        keys = []
        values = []
        for key, value in sorted_data:
            keys.append(key)
            values.append(value)
        _cases.append(
            {
                "keys": keys,
                "values": values,
                "root": bytes.fromhex(case["output"]["merkleRoot"]),
            }
        )

    return _cases


test_cases = get_cases()


def test_batch_update_fixtures(capsys):
    for case in test_cases:
        asyncio.run(batch_test(case, capsys))


async def batch_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]

    _smt = smt.SparseMerkleTree()

    assert _smt.root.hash == EMPTY_HASH
    new_root = await _smt.update(keys, values)

    assert _smt.root.hash == root == new_root.hash
