from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.constants import EMPTY_HASH
import time
import asyncio
from tests.tree.utils import create_test_case

KEY_LENGTH = 32


def test_large_update(capsys) -> None:
    start_time = time.time()
    initial_keys, initial_values = create_test_case(1000000)
    extra_keys, extra_values = create_test_case(10000)

    with capsys.disabled():
        print(f"\ncreate test cases: {time.time() - start_time:.2f}s")
    asyncio.run(
        case_testing_batch(
            initial_keys, initial_values, extra_keys, extra_values, capsys
        )
    )


async def case_testing_batch(
    initial_keys, initial_values, extra_keys, extra_values, capsys
) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree(KEY_LENGTH)
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _smt.update(initial_keys, initial_values)
    assert _smt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create tree with {len(initial_keys)} leaves: {time.time() - start_time:.2f}s"
        )

    start_time = time.time()
    extra_new_root = await _smt.update(extra_keys, extra_values)
    assert _smt.root.hash == extra_new_root.hash
    with capsys.disabled():
        print(
            f"update tree with {len(extra_keys)} leaves: {time.time() - start_time:.2f}s"
        )

    return _smt
