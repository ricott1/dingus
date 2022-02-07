from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.skip_merkle_tree import SkipMerkleTree
from dingus.tree.constants import EMPTY_HASH
import time
import asyncio
import os

KEY_LENGTH = 32


def create_test_case(n: int, key_length: int = KEY_LENGTH) -> list[tuple[bytes, bytes]]:
    return [(os.urandom(key_length), os.urandom(32)) for _ in range(n)]


def test_update(capsys) -> None:
    start_time = time.time()
    initial_case = create_test_case(50)
    extra_case = create_test_case(40)
    with capsys.disabled():
        print(f"\ncreate test cases: {time.time() - start_time:.2f}s")

    # update_smt = asyncio.run(case_testing(initial_case, extra_case, capsys))
    # in_batch_smt = asyncio.run(case_testing_batch(initial_case, [], capsys))
    # in_skip_smt = asyncio.run(case_testing_skip(initial_case, [], capsys))

    batch_smt = asyncio.run(case_testing_batch(initial_case, extra_case, capsys))
    skip_smt = asyncio.run(case_testing_skip(initial_case, extra_case, capsys))


    if not batch_smt.root.hash == skip_smt.root.hash:
        print("\n BATCH TREE")
        print(asyncio.run(in_batch_smt.print(in_batch_smt.root)))
        print(asyncio.run(batch_smt.print(batch_smt.root)))
        print("\n SKIP TREE")
        print(asyncio.run(in_skip_smt.print(in_skip_smt.root)))
        print(asyncio.run(skip_smt.print(skip_smt.root)))

    assert batch_smt.root.hash == skip_smt.root.hash


async def case_testing(
    initial_case, extra_case, capsys
) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree(KEY_LENGTH)
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    for k, v in initial_case:
        new_root = await _smt.update(k, v)
        assert _smt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create tree with {len(initial_case)} leaves: {time.time() - start_time:.2f}s"
        )

    _smt.stats = {
        "db_set": 0,
        "db_get": 0,
        "db_delete": 0,
        "hashes": 0,
        "leaf_created": 0,
        "branch_created": 0,
        "update_calls": 0,
    }
    start_time = time.time()
    for k, v in extra_case:
        extra_new_root = await _smt.update(k, v)
        assert _smt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(
            f"update tree with {len(extra_case)} leaves: {time.time() - start_time:.2f}s"
        )
        print(_smt.stats)
    return _smt


async def case_testing_batch(
    initial_case, extra_case, capsys
) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree(KEY_LENGTH, db="rocksdb")
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _smt.update_batch(initial_case, strict=True)
    assert _smt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create tree with {len(initial_case)} leaves: {time.time() - start_time:.2f}s"
        )

    _smt.stats = {
        "db_set": 0,
        "db_get": 0,
        "db_delete": 0,
        "hashes": 0,
        "leaf_created": 0,
        "branch_created": 0,
        "update_calls": 0,
    }
    start_time = time.time()
    extra_new_root = await _smt.update_batch(extra_case)
    assert _smt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(
            f"update tree with {len(extra_case)} leaves: {time.time() - start_time:.2f}s"
        )
        print(_smt.stats)
        
    return _smt

async def case_testing_skip(
    initial_case, extra_case, capsys
) -> Coroutine[None, None, SparseMerkleTree]:
    _skmt = SkipMerkleTree(KEY_LENGTH, db="rocksdb")
    assert _skmt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _skmt.update(initial_case, strict=True)
    assert _skmt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create tree with {len(initial_case)} leaves: {time.time() - start_time:.2f}s"
        )

    _skmt.stats = {
        "db_set": 0,
        "db_get": 0,
        "db_delete": 0,
        "hashes": 0,
        "leaf_created": 0,
        "branch_created": 0,
        "update_subtree_calls": 0,
        "update_node_calls": 0,
    }
    start_time = time.time()
    extra_new_root = await _skmt.update(extra_case)
    assert _skmt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(
            f"update tree with {len(extra_case)} leaves: {time.time() - start_time:.2f}s"
        )
        print(_skmt.stats)

    return _skmt
