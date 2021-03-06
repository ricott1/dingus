from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt
import dingus.tree.sparse_merkle_tree as smt
from dingus.tree.skip_merkle_tree import is_inclusion_proof, verify
from dingus.tree.types import Proof, Query

def get_cases() -> list[dict]:
    _cases = []
    with open("tests/tree/fixtures/smt_jumbo.json", "r") as f:
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

async def skip_test(case, capsys):
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    delete_keys = case["delete_keys"]
    query_keys = case["query_keys"]
    fixture_proof: Proof = case["proof"]

    _skmt = skmt.SkipMerkleTree()

    assert _skmt.root.hash == EMPTY_HASH
    new_root = await _skmt.update(keys, values)
    new_root = await _skmt.update(delete_keys, [b"" for _ in delete_keys])

    assert _skmt.root.hash == root == new_root.hash
    proof = await _skmt.generate_proof(query_keys)

    assert len(proof.queries) == len(fixture_proof.queries)
    for query, fixture_query in zip(proof.queries, fixture_proof.queries):
        assert query.key == fixture_query.key
        assert query.value == fixture_query.value 
        assert query.bitmap == fixture_query.bitmap

    assert proof.queries == fixture_proof.queries
    assert proof.sibling_hashes == fixture_proof.sibling_hashes
    assert verify(query_keys, proof, root)
    for k, q in zip(query_keys, proof.queries):
        if k in keys and not k in delete_keys:
            assert is_inclusion_proof(k, q) == True
        else:
            assert is_inclusion_proof(k, q) == False

    # Delete first 25% of query key
    extra_delete_keys = query_keys[:len(query_keys)//4]
    extra_root = await _skmt.update(extra_delete_keys, [b"" for _ in extra_delete_keys])
    extra_proof = await _skmt.generate_proof(extra_delete_keys)
    assert verify(extra_delete_keys, extra_proof, extra_root.hash)
    for k, q in zip(query_keys, extra_proof.queries):
        if k in extra_delete_keys:
            assert is_inclusion_proof(k, q) == False
        elif k in keys and not k in extra_delete_keys:
            assert is_inclusion_proof(k, q) == True
        else:
            assert is_inclusion_proof(k, q) == False