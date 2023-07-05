import asyncio
import os
import random
from dingus.tree.skip_merkle_tree import SkipMerkleTree, is_inclusion_proof, verify
from dingus.tree.constants import LEAF_PREFIX, BRANCH_PREFIX
from dingus.crypto import hash
import json

from dingus.tree.types import Proof



filename = "./fixtures/fixtures_delete_non_inclusion_proof.json"
script_dir = os.path.dirname(__file__)
KEY_LENGTH = 32

async def create_fixtures(N: int, D: int, Q: int, insertion_orders: int) -> None:

    print("Creating new fixtures in:", os.path.join(script_dir, filename))
    
    with open(os.path.join(script_dir, "fixtures/fixture_template.json"), "r") as f:
        fixture = json.load(f)
    print (fixture["testCases"])
    for n in range(1, 20):
        test_cases = [await get_fixture(100*n, (100*n)//4, (100*n)//8, i, False) for i in range(insertion_orders)]
        fixture["testCases"] += test_cases
    with open(os.path.join(script_dir, filename), "w") as f:
        json.dump(fixture, f, indent=4)
        

async def get_fixture(N: int, D: int, Q: int, i:int, inclusion_proof:bool=True) -> dict:
    
    keys = [hash(f"LSK_FIXTURES_{n}".encode("ascii")) for n in range(N)]
    if i > 0: random.shuffle(keys)
    values = [hash(k) for k in keys]
    
    delete_keys = keys[:D//2] + [hash(f"LSK_DELETE_{d}".encode("ascii")) for d in range(D//2)]
    query_keys = keys[:Q] if inclusion_proof else delete_keys[:Q]

    description = f"Given key-value entries: {len(keys)}, deleting {len(delete_keys)}, querying {len(query_keys)}. Order of insertion: {i}."

    _skmt = SkipMerkleTree()

    new_root = await _skmt.update(keys, values)
    new_root = await _skmt.update(delete_keys, [b"" for _ in delete_keys])
    
    assert _skmt.root.hash == new_root.hash


    # Filter query keys to only have inclusion proofs
    # query_keys = [k for k in query_keys if k in keys and not k in delete_keys]
    if query_keys:
        proof = await _skmt.generate_proof(query_keys)
        sibling_hashes = [s.hex() for s in proof.sibling_hashes]
        
        assert verify(query_keys, proof, _skmt.root.hash)

        for k, q in zip(query_keys, proof.queries):
            if k in keys and not k in delete_keys:
                assert is_inclusion_proof(k, q) == True
            else:
                assert is_inclusion_proof(k, q) == False

        for k, q in zip(query_keys, proof.queries):
            assert is_inclusion_proof(k, q) == inclusion_proof
    else:
        proof = Proof([], [])
        sibling_hashes = []
    
    # Delete first 25% of query key
    # extra_delete_keys = query_keys[:len(query_keys)//4]
    # extra_root = await _skmt.update(extra_delete_keys, [b"" for _ in extra_delete_keys])

    # # Now recreate proof
    # random.shuffle(query_keys)
    # extra_proof = await _skmt.generate_proof(query_keys)
    
    # assert verify(query_keys, extra_proof, extra_root.hash)
    # # print([s.hex() for s in extra_proof.sibling_hashes])
    # for k, q in zip(query_keys, extra_proof.queries):
    #     if (k in keys) and not (k in extra_delete_keys + delete_keys):
    #         assert is_inclusion_proof(k, q) == True
    #     else:
    #         assert is_inclusion_proof(k, q) == False
    
    queries = [
        {
            "bitmap": f"{q.bitmap.hex()}",
            "key": f"{q.key.hex()}",
            "value": f"{q.value.hex()}"
        } for q in proof.queries
    ]

    return {
        "description": description,
        "input": {
            "keys": [f"{k.hex()}" for k in keys],
            "values": [f"{v.hex()}" for v in values],
            "deleteKeys": [f"{k.hex()}" for k in delete_keys],
            "queryKeys": [f"{k.hex()}" for k in query_keys]
        },
        "output": {
            "merkleRoot": f"{_skmt.root.hash.hex()}",
            "proof": {
                "siblingHashes": sibling_hashes,
                "queries": queries
            }
        }
    }
        





if __name__ == "__main__":
    N = 2000
    D = 0
    Q = 0
    insertion_orders = 3
    asyncio.run(create_fixtures(N, D, Q, insertion_orders))