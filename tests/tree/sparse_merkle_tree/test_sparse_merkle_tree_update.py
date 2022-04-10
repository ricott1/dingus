from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.skip_merkle_tree import SkipMerkleTree
from tests.tree.utils import create_test_case
from dingus.tree.constants import EMPTY_HASH
import time
import asyncio


def test_update(capsys) -> None:
    start_time = time.time()
    initial_keys, initial_values = create_test_case(10000)
    extra_keys, extra_values = initial_keys[:20], initial_values[:20]
    with capsys.disabled():
        print(f"\ncreate test cases: {time.time() - start_time:.2f}s")

    batch_smt = asyncio.run(
        case_testing_batch(
            initial_keys, initial_values, extra_keys, extra_values, capsys
        )
    )
    # skip_smt = asyncio.run(case_testing_skip(initial_keys, initial_values, extra_keys, extra_values, capsys))

    # assert batch_smt.root.hash == skip_smt.root.hash


async def case_testing_batch(
    initial_keys, initial_values, extra_keys, extra_values, capsys
) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree()
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _smt.update(initial_keys, initial_values)
    assert _smt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create SMT tree with {len(initial_keys)} leaves: {time.time() - start_time:.2f}s"
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
    extra_new_root = await _smt.update(extra_keys, extra_values)
    assert _smt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(
            f"update SMT tree with {len(extra_keys)} leaves: {time.time() - start_time:.2f}s"
        )
        print(_smt.stats)

    return _smt


async def case_testing_skip(
    initial_keys, initial_values, extra_keys, extra_values, capsys
) -> Coroutine[None, None, SparseMerkleTree]:
    _skmt = SkipMerkleTree()
    assert _skmt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _skmt.update(initial_keys, initial_values)
    assert _skmt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create SKMT tree with {len(initial_keys)} leaves: {time.time() - start_time:.2f}s"
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
    extra_new_root = await _skmt.update(extra_keys, extra_values)
    assert _skmt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(
            f"update SKMT tree with {len(extra_keys)} leaves: {time.time() - start_time:.2f}s"
        )
        print(_skmt.stats)

    return _skmt
