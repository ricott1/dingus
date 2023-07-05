import os
from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt
import dingus.tree.sparse_merkle_tree as smt
from os import path

from dingus.tree.types import Proof, Query

dir_name = path.dirname(__file__)
filename = path.join(dir_name, "fixtures/fixtures_no_delete_inclusion_proof.json")

def get_cases() -> list[dict]:
    _cases = []
    print("testing", filename)
    with open(filename, "r") as f:
        test_cases = json.load(f)["testCases"]
    for case in test_cases:
        queries = [Query(bytes.fromhex(q["key"]), bytes.fromhex(q["value"]), bytes.fromhex(q["bitmap"])) for q in case["output"]["proof"]["queries"]]
        _cases.append({
            "description": case["description"],
            "keys": [bytes.fromhex(i) for i in case["input"]["keys"]],
            "delete_keys": [bytes.fromhex(i) for i in case["input"]["deleteKeys"]],
            "values": [bytes.fromhex(i) for i in case["input"]["values"]],
            "root": bytes.fromhex(case["output"]["merkleRoot"]),
            "query_keys" : [bytes.fromhex(i) for i in case["input"]["queryKeys"]],
            "proof": Proof(
                [bytes.fromhex(i) for i in case["output"]["proof"]["siblingHashes"]],
                queries
            )
        })

    return _cases

test_cases = get_cases()


def test_skip_merkle_tree_fixtures(capsys):
    for case in test_cases:
        asyncio.run(skip_test(case, capsys))


async def skip_test(case, capsys, inclusion_proof=True):
    print("test >> ", case["description"])
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    delete_keys = case["delete_keys"]
    query_keys = case["query_keys"]
    proof = case["proof"]

    _skmt = skmt.SkipMerkleTree()
    assert _skmt.root.hash == EMPTY_HASH
    new_root = await _skmt.update(keys, values)

    _smt = smt.SparseMerkleTree()
    assert _smt.root.hash == EMPTY_HASH
    smt_new_root = await _smt.update(keys, values)

    assert _smt.root.hash == _skmt.root.hash == smt_new_root.hash == new_root.hash


    new_root = await _skmt.update(delete_keys, [b"" for _ in delete_keys])
    assert _skmt.root.hash == root == new_root.hash
    # proof.sibling_hashes = [os.urandom(32)] + proof.sibling_hashes
    assert skmt.verify(query_keys, proof, _skmt.root.hash)
    print(len(proof.sibling_hashes))

    for k, q in zip(query_keys, proof.queries):
        if k in keys and not k in delete_keys:
            assert skmt.is_inclusion_proof(k, q) == True
        else:
            assert skmt.is_inclusion_proof(k, q) == False

    for k, q in zip(query_keys, proof.queries):
        assert skmt.is_inclusion_proof(k, q) == inclusion_proof

if __name__ == "__main__":
    test_skip_merkle_tree_fixtures(None)
