from dingus.tree.sparse_merkle_tree import SparseMerkleTree
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
    values = case["values"]
    root = case["root"]
    
    _skmt = SparseMerkleTree()

    assert _skmt.root.hash == _skmt.hasher.empty
    
    update_root: SubTree = await _skmt.update(keys, values)
    
    
    # delete_keys = keys[:4]
    new_root: SubTree = await _skmt.delete(delete_keys)
    
    if not _skmt.root.hash == new_root.hash == root:
        # print(f"UT ROOT: {_skmt.root.hash.hex()} {update_root.hash.hex()}")
        print("CASE:", len(keys))
        print(f"DROOT: {new_root.hash.hex()} {new_root.hash.hex()}")

    assert _skmt.root.hash == new_root.hash == root

