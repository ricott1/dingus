from dingus.tree.constants import EMPTY_HASH
import json
import asyncio
import dingus.tree.skip_merkle_tree as skmt
import dingus.tree.sparse_merkle_tree as smt
from dingus.tree.skip_merkle_tree import is_inclusion_proof, verify
from dingus.tree.types import Proof, Query

def get_cases() -> list[dict]:
    test_cases = [
        {
            "description": "Given key-value entries: 5, deleting 0, querying 2. Order of insertion: 1.",
            "input": {
                "keys": [
                    "043aaee7ccfb1a64f6d7bcd46657c27cb1f4569ae9e7c03445bd6c6fd013109b",
                    "35af2d15ebde4d67b29569ec19749e813c76f02286afc5a2a9871c2bfbdaab32",
                    "c19a797fa1fd590cd2e5b42d1cf5f246e29b91684e2f87404b81dc345c7a56a0",
                    "049488d869cbef080602a371ab0d39d97af103fb726aaeb02ccd36c06f494e5d",
                    "5bad0d1132ac152cf657be8918ae163578448d56d40def9a590fe3dcab0c339b"
                ],
                "values": [
                    "b8d05a8c46c9d51b97acb64d7531e3df8fc48adc64511b70cc3a258231ec775c",
                    "5a563c34ebb8c0797c211427801c25f542b2e547e3c0fddf244c188eebde9fc2",
                    "a936dca5e1a3253a18dda01283d0870f60cffebf4a592ecacec9b0d700e9498a",
                    "0daa5c9173acd494e93af7e26d8d976b8adacdd671b047f19efe84fd8b10e03e",
                    "0a57afdf7301c3717c6d44ea667336452a8c79a1156f1e01eec3473fe2d6b2e6"
                ],
                "deleteKeys": [],
                "queryKeys": [
                    "043aaee7ccfb1a64f6d7bcd46657c27cb1f4569ae9e7c03445bd6c6fd013109b",
                    "5bad0d1132ac152cf657be8918ae163578448d56d40def9a590fe3dcab0c339b",
                    "0c9488d869cbef080602a371ab0d39d97af103fb726aaeb02ccd36c06f494e5d"
                ]
            },
            "output": {
                "merkleRoot": "724499977b2da62a95e6d62079192e2c3649fbe1c52cc971232f0075c405508c",
                "proof": {
                    "siblingHashes": [
                        "b993d789f99cd52b96e04b0df9306f230dfecfd4e034d1a511cd8252e8533c82",
"                        9d1f1081ebf3bd7e1065be72d0e24c3bd0d65281c4e8f8d52a4a08ee0e744665",
"                        58589f68d23968a87a164be3d2cfe47da3375345442820777f881be406d98e56"
                    ],
                    "queries": [
                        {
                            "bitmap": "0109",
                            "key": "043aaee7ccfb1a64f6d7bcd46657c27cb1f4569ae9e7c03445bd6c6fd013109b",
                            "value": "b8d05a8c46c9d51b97acb64d7531e3df8fc48adc64511b70cc3a258231ec775c"
                        },
                        {
                            "bitmap": "03",
                            "key": "5bad0d1132ac152cf657be8918ae163578448d56d40def9a590fe3dcab0c339b",
                            "value": "0a57afdf7301c3717c6d44ea667336452a8c79a1156f1e01eec3473fe2d6b2e6"
                        },
                        {
                            "bitmap": "17",
                            "key": "0c9488d869cbef080602a371ab0d39d97af103fb726aaeb02ccd36c06f494e5d",
                            "value": ""
                        }
                    ]
                }
            }
        }
    ]

    _cases = []
    for case in test_cases:
        _cases.append({
            "description": case["description"],
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

async def skip_test(case, capsys = None):
    description = case["description"]
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
    print(new_root.hash.hex())
    assert _skmt.root.hash == root == new_root.hash
    print(await _skmt.print())


    proof = await _skmt.generate_proof(query_keys)
    print("Proof")
    for query in proof.queries:
        print(query.key.hex())
        print(query.value.hex())
        print(query.bitmap.hex())

    print("Siblings")
    for h in proof.sibling_hashes:
        print(h.hex())

    

    # assert len(proof.queries) == len(fixture_proof.queries)
    # for query, fixture_query in zip(proof.queries, fixture_proof.queries):
    #     assert query.key == fixture_query.key
    #     assert query.value == fixture_query.value 
    #     assert query.bitmap == fixture_query.bitmap

    # assert proof.queries == fixture_proof.queries
    # assert proof.sibling_hashes == fixture_proof.sibling_hashes



    print("CASE:", description)
    assert verify(query_keys, fixture_proof, root)

    for k, q in zip(query_keys, proof.queries):
        if k in keys and not k in delete_keys:
            assert is_inclusion_proof(k, q) == True
        else:
            assert is_inclusion_proof(k, q) == False
    
    return

    # Delete first 25% of query key
    extra_delete_keys = query_keys[:len(query_keys)//4]
    extra_root = await _skmt.update(extra_delete_keys, [b"" for _ in extra_delete_keys])

    # Now recreate proof
    extra_proof = await _skmt.generate_proof(query_keys)
    assert verify(query_keys, extra_proof, extra_root.hash)
    # print([s.hex() for s in extra_proof.sibling_hashes])
    for k, q in zip(query_keys, extra_proof.queries):
        if (k in keys) and not (k in extra_delete_keys + delete_keys):
            assert is_inclusion_proof(k, q) == True
        else:
            assert is_inclusion_proof(k, q) == False

    # print([(q.key.hex(), q.value.hex(), q.bitmap.hex()) for q in extra_proof.queries])


if __name__ == "__main__":
    test_skip_merkle_tree_fixtures(None)