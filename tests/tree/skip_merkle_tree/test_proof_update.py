import copy
import os
import random
from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt
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


async def recovery_plugin_flow(capsys):
    
    case = test_cases[0]
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    query_keys = case["query_keys"]
    Q = len(query_keys)
    
    _skmt = skmt.SkipMerkleTree()
    assert _skmt.root.hash == EMPTY_HASH
    base_merkle_root = await _skmt.update(keys, values)
    assert base_merkle_root.hash == root

    # 1. get initial proof for monitored keys: monitored_proof
    monitored_keys = random.sample(query_keys, Q//2)
    monitored_proof = await _skmt.generate_proof(monitored_keys)
    print("\nmonitored proof", monitored_proof)

    # 2. get additional proof someone else posted: sneak_proof
    sneak_keys = set(random.sample(query_keys, Q//2) + random.sample(monitored_keys, 1))
    sneak_proof = await _skmt.generate_proof(sneak_keys)
    print("\nsneak proof", sneak_proof)
    
    # 3. remove overlapping keys from monitored_proof
    removing_keys = [k for k in monitored_keys if k in sneak_keys]
    print("removing_keys", [k.hex() for k in removing_keys])
    assert len(removing_keys) > 0
    no_overlap_proof = skmt.remove_keys_from_proof(copy.deepcopy(monitored_proof), removing_keys)
    print("\nno overlap proof", no_overlap_proof)

    # 4. update no_overlap_proof with sneak_proof
    # voided proof is the proof after setting queried nodes hash to empty hash
    voided_proof = Proof([s for s in sneak_proof.sibling_hashes], [Query(q.key, EMPTY_HASH, q.bitmap) for q in sneak_proof.queries])
    visited_nodes = skmt.get_visited_nodes(voided_proof.sibling_hashes, voided_proof.queries)
    nodes_override_mapping = skmt.get_nodes_override_mapping(copy.deepcopy(no_overlap_proof.sibling_hashes), copy.deepcopy(no_overlap_proof.queries), visited_nodes)
    
    final_proof = no_overlap_proof
    for h1, h2 in nodes_override_mapping.items():
        idx = final_proof.sibling_hashes.index(h1)
        final_proof.sibling_hashes[idx] = h2
    print("\nfinal proof", final_proof)

    # 5. the final proof is checked
    final_root = skmt.calculate_root(copy.deepcopy(final_proof.sibling_hashes), copy.deepcopy(final_proof.queries))
    assert final_root == visited_nodes["root"]
    assert final_root != base_merkle_root.hash
    print("base root", base_merkle_root.hash.hex())
    print("new_root ", final_root.hex())


async def test_remove_keys_from_proof(capsys):
    case = random.sample(test_cases, 1)[0]
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    query_keys = case["query_keys"]
    Q = len(query_keys)

    print("\nquery keys", [k.hex()[:4] for k in query_keys])
    removing_keys = random.sample(query_keys, Q//2)
    print("\nremoving_keys", [k.hex()[:4] for k in removing_keys])
    new_query_keys = [k for k in query_keys if k not in removing_keys]
    print("\n new query keys", [k.hex()[:4] for k in new_query_keys])

    _skmt = skmt.SkipMerkleTree()
    assert _skmt.root.hash == EMPTY_HASH
    base_merkle_root = await _skmt.update(keys, values)
    assert base_merkle_root.hash == root
    # print(await _skmt.print())

    # Just a check :)
    assert skmt.verify(query_keys, await _skmt.generate_proof(query_keys), base_merkle_root.hash) == True
    
    base_proof = await _skmt.generate_proof(query_keys)
    updated_proof = skmt.remove_keys_from_proof(copy.deepcopy(base_proof), removing_keys)
    print("\nupdated_proof", updated_proof)

    # Check that indeed the updated proof does not contain the removed keys
    for k in new_query_keys:
        assert k in [q.key for q in updated_proof.queries]
    for k in removing_keys:
        assert k not in [q.key for q in updated_proof.queries]

    # Check that the update proof is still a valid proof against the same Merkle root
    assert skmt.verify(new_query_keys, updated_proof, base_merkle_root.hash) == True

async def test_proof_update(capsys):
    case = test_cases[2]
    keys = case["keys"]
    values = case["values"]
    root = case["root"]
    query_keys = case["query_keys"]
    Q = len(query_keys)

    _skmt = skmt.SkipMerkleTree()
    assert _skmt.root.hash == EMPTY_HASH
    base_merkle_root = await _skmt.update(keys, values)
    assert base_merkle_root.hash == root
    print("\nbase root", base_merkle_root.hash.hex())

    # Base proof that we need to update after nodes have been emptied
    base_proof = await _skmt.generate_proof(query_keys[:Q//2])
    # Proof that empties the nodes
    merging_proof = await _skmt.generate_proof(query_keys[Q//2:])
    voided_proof = Proof([s for s in merging_proof.sibling_hashes], [Query(q.key, EMPTY_HASH, q.bitmap) for q in merging_proof.queries])
    
    # Check that the voided proof indeed verifies the updated state root
    visited_nodes = skmt.get_visited_nodes(copy.deepcopy(voided_proof.sibling_hashes), copy.deepcopy(voided_proof.queries))
    new_root = skmt.calculate_root_with_visited_nodes_override(copy.deepcopy(base_proof.sibling_hashes), copy.deepcopy(base_proof.queries), visited_nodes)
    voided_root = skmt.calculate_root(copy.deepcopy(voided_proof.sibling_hashes), copy.deepcopy(voided_proof.queries))
    assert new_root == voided_root == visited_nodes["root"]
    
    nodes_override_mapping = skmt.get_nodes_override_mapping(copy.deepcopy(base_proof.sibling_hashes), copy.deepcopy(base_proof.queries), visited_nodes)

    for h1, h2 in nodes_override_mapping.items():
        idx = base_proof.sibling_hashes.index(h1)
        base_proof.sibling_hashes[idx] = h2


    voided_root_from_base_proof = skmt.calculate_root(copy.deepcopy(voided_proof.sibling_hashes), copy.deepcopy(voided_proof.queries))
    assert new_root == voided_root_from_base_proof == visited_nodes["root"]
    assert new_root != base_merkle_root
    print("new_root", new_root.hex())

if __name__ == "__main__":
    asyncio.run(recovery_plugin_flow(None))
