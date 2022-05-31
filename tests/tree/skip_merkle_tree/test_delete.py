from dingus.tree.skip_merkle_tree import SkipMerkleTree
from dingus.tree.types import SubTree
import json
import asyncio

def get_cases() -> list[dict]:
    _cases = []
    with open("tests/tree/fixtures/remove_tree.json", "r") as f:
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
    delete_keys = case["delete_keys"]
    delete_values = [b"" for k in delete_keys]
    values = case["values"]
    root = case["root"]
    update_keys = []
    update_values = []
    for i in range(len(keys)):
        if keys[i] not in delete_keys:
            update_keys.append(keys[i])
            update_values.append(values[i])

    _skmt = SkipMerkleTree()

    assert _skmt.root.hash == _skmt.hasher.empty
    update_root: SubTree = await _skmt.update(keys, values)
    
    
    await _skmt.update(delete_keys[:3], delete_values[:3])
    # await _skmt.update(delete_keys, delete_values)
    await _skmt.update(keys, values)
    new_root = await _skmt.update(delete_keys, delete_values)
    
    only_update_root: SubTree = await SkipMerkleTree().update(update_keys, update_values)
    assert _skmt.root.hash == new_root.hash == root == only_update_root.hash

