from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.constants import EMPTY_HASH
import asyncio
import os

TOKEN_MODULE_ID = b"\x02"
STORE_PREFIX_USER = b"\x00\x00"
STORE_PREFIX_SUPPLY = b"\x80\x00"
STORE_PREFIX_ESCROW = b"\xc0\x00"
STORE_PREFIX_AVAILABLE_LOCAL_ID = b"\xd0\x00"
STORE_PREFIX_TERMINATED_ESCROW = b"\xe0\x00"

def create_test_case(n: int) -> list[tuple[bytes, bytes]]:
    return [(os.urandom(32), os.urandom(32)) for _ in range(n)]

def test_update() -> None:
    n_user = 2
    n_supply = 1
    n_escrow = 2

    user_data = create_test_case(n_user)
    supply_data = create_test_case(n_supply)
    escrow_data = create_test_case(n_escrow)

    user_smt = asyncio.run(create_tree(user_data))
    supply_smt = asyncio.run(create_tree(supply_data))
    escrow_smt = asyncio.run(create_tree(escrow_data))


    

    partial_smt = asyncio.run(create_tree([
        (TOKEN_MODULE_ID + STORE_PREFIX_USER, user_smt.root.hash),
        # (TOKEN_MODULE_ID + STORE_PREFIX_SUPPLY, supply_smt.root.hash),
        # (TOKEN_MODULE_ID + STORE_PREFIX_ESCROW, escrow_smt.root.hash),
    ], True))

    
    token_store_data = [(TOKEN_MODULE_ID + STORE_PREFIX_USER + key, value) for key, value in user_data] 
        # [(TOKEN_MODULE_ID + STORE_PREFIX_SUPPLY + key, value) for key, value in supply_data]
        # [(TOKEN_MODULE_ID + STORE_PREFIX_ESCROW + key, value) for key, value in escrow_data]

    token_smt = asyncio.run(create_tree(token_store_data, True))

    assert token_smt.root.hash == partial_smt.root.hash
    

async def create_tree(data, print_tree: bool = False) -> Coroutine[None, None, SparseMerkleTree]:
    key_length = len(data[0][0])
    _smt = SparseMerkleTree(key_length)
    assert _smt.root.hash == EMPTY_HASH
    
    new_root = await _smt.update_batch(data, strict = True)
    assert _smt.root.hash == new_root.hash

    if print_tree:
        print(await _smt.print(_smt.root))

    return _smt

