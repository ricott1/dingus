import os
from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt
import dingus.tree.sparse_merkle_tree as smt
from dingus.tree.skip_merkle_tree import is_inclusion_proof, verify
from dingus.tree.types import Proof, Query, SubTree


def get_cases() -> list[dict]:
    _cases = []
    with open("tests/tree/fixtures/smt_proof.json", "r") as f:
        test_cases = json.load(f)["testCases"]
    for case in test_cases:
        _cases.append({
            "keys": [bytes.fromhex(i) for i in case["input"]["keys"]],
            "delete_keys": [bytes.fromhex(i) for i in case["input"]["deleteKeys"]],
            "query_keys": [bytes.fromhex(i) for i in case["input"]["queryKeys"]],
            "values": [bytes.fromhex(i) for i in case["input"]["values"]],
            "root": bytes.fromhex(case["output"]["merkleRoot"]),
            "proof": Proof([bytes.fromhex(h) for h in case["output"]["proof"]["siblingHashes"]], [Query(bytes.fromhex(q["key"]), bytes.fromhex(q["value"]), bytes.fromhex(q["bitmap"])) for q in case["output"]["proof"]["queries"]])
        })

    return _cases


test_cases = get_cases()

def test_skip_merkle_tree_fixtures(capsys):
    for case in test_cases:
        asyncio.run(skip_test(case, capsys))

def test_skip_merkle_tree_inclusion_and_non_inclusion(capsys):
    for case in test_cases:
        asyncio.run(skip_random_test(case, capsys))

async def skip_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    query_keys = case["query_keys"]
    fixture_proof: Proof = case["proof"]

    _skmt = skmt.SkipMerkleTree()

    assert _skmt.root.hash == EMPTY_HASH
    new_root = await _skmt.update(keys, values)
    assert _skmt.root.hash == root == new_root.hash

    # _smt = smt.SparseMerkleTree()
    # new_root = await _smt.update(keys, values)
    # assert _smt.root.hash == root == new_root.hash
    # assert _skmt.root.hash == _smt.root.hash
    # print(await _smt.print(_smt.root))

    proof = await _skmt.generate_proof(query_keys)

    assert len(proof.queries) == len(fixture_proof.queries)
    for query, fixture_query in zip(proof.queries, fixture_proof.queries):
        assert query.key == fixture_query.key
        assert query.value == fixture_query.value 
        assert query.bitmap == fixture_query.bitmap

    assert proof.queries == fixture_proof.queries
    assert proof.sibling_hashes == fixture_proof.sibling_hashes
    assert verify(query_keys, proof, root)


async def skip_random_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    query_keys = case["query_keys"]

    _skmt = skmt.SkipMerkleTree()

    assert _skmt.root.hash == EMPTY_HASH
    new_root: SubTree = await _skmt.update(keys, values)
    assert _skmt.root.hash == root == new_root.hash


    _smt = smt.SparseMerkleTree()
    new_root = await _smt.update(keys, values)
    assert _smt.root.hash == root == new_root.hash
    assert _skmt.root.hash == _smt.root.hash
    
    random_queries = [os.urandom(32) for _ in range(32)] + query_keys
    
    random_proof = await _skmt.generate_proof(random_queries) 
    assert verify(random_queries, random_proof, _skmt.root.hash)
    for k, q in zip(random_queries, random_proof.queries):
        if k in query_keys:
            assert is_inclusion_proof(k, q) == True
        else:
            assert is_inclusion_proof(k, q) == False

    del_root: SubTree = await _skmt.update([query_keys[0]], [b''])
    delete_proof = await _skmt.generate_proof(random_queries) 
    assert verify(random_queries, delete_proof, del_root.hash)
    assert is_inclusion_proof(query_keys[0], delete_proof.queries[0]) == False
