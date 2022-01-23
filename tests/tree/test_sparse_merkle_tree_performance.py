from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree, TreeNode
from dingus.tree.constants import EMPTY_HASH
import time
import asyncio
import os

KEY_LENGTH = 32

def create_test_case(n: int, key_length: int = KEY_LENGTH) -> list[tuple[bytes, bytes]]:
    return [(os.urandom(key_length), os.urandom(32)) for _ in range(n)]

def test_large_update(capsys) -> None:
    start_time = time.time()
    initial_case = create_test_case(10000000)
    extra_case = create_test_case(10000)
    with capsys.disabled():
        print(f"\nTEST TIME CASES: {time.time() - start_time:.2f}s")
    asyncio.run(case_testing_batch(initial_case, extra_case, capsys))

async def case_testing_batch(initial_case, extra_case, capsys) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree(KEY_LENGTH)
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _smt.update_batch(initial_case)
    assert _smt.root.hash == new_root.hash
    with capsys.disabled():
        print(f"\nTEST TIME BATCH {len(initial_case)}: {time.time() - start_time:.2f}s")

    start_time = time.time()
    extra_new_root = await _smt.update_batch(extra_case)
    assert _smt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(f"\nTEST TIME BATCH {len(extra_case)}: {time.time() - start_time:.2f}s")

    return _smt

