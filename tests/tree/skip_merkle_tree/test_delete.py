from dingus.tree.skip_merkle_tree import SkipMerkleTree
from dingus.tree.types import SubTree
from dingus.utils import hash
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

    # keys = [
    #     bytes.fromhex("631b1310c6dae382f611f97639cfa8ce2033fc3633a53c1ff79dc51289b1fc14"),
    #     bytes.fromhex("45b75c5966dff8a1e918460a18eb9560c7cb5163d79d6fc9fac582b9699dbb69"),
    #     bytes.fromhex("39d167e3d5e34068b5ca4ec54e3a33492428d6cbeac6f5021a5dfb14bce7ddb5"),
    #     bytes.fromhex("25ef1d05296e4e92ff24e47fb85fcbd0d681b08ca23e5feb685c35679fd42360"),
    #     bytes.fromhex("ac7d8fc0eebbb340c197db3acea85388636610edbf84a83d36425a8b42928116"),
    #     bytes.fromhex("8cc62b70acaf8212cf6c0b28b030e640d926cdff2f3dff30ddb47b217a8cf734"),
    #     bytes.fromhex("f01251297cf97c7ac9b36b24d351e2630e6e11c4f203e57f8cc2181296a69063"),
    #     bytes.fromhex("2b1f32f030c9c0f6d696606487cd03184e26e664fd75ec7e682f1ddcc57228cf"),
    # ]
    
    # values = [hash(k) for k in keys]
    # root = bytes.fromhex("2ed318fb764f81ddb6dea6266c997805dc1c07335ad17dfcd7922fdc3af581c2")
    
    

    _skmt = SkipMerkleTree()

    assert _skmt.root.hash == _skmt.hasher.empty
    update_root: SubTree = await _skmt.update(keys, values)
    
    delete_values = [b"" for k in delete_keys]
    new_root: SubTree = await _skmt.update(delete_keys[:3], delete_values[:3])
    new_root: SubTree = await _skmt.update(delete_keys, delete_values)
    if not _skmt.root.hash == new_root.hash == root:
        # print(f"UT ROOT: {_skmt.root.hash.hex()} {update_root.hash.hex()}")
        print("CASE:", len(keys))
        print(f"DROOT: {new_root.hash.hex()} {root.hex()}")
    assert _skmt.root.hash == new_root.hash == root

