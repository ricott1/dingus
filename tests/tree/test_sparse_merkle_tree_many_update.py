from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.constants import EMPTY_HASH
import asyncio
import os

KEY_LENGTH = 32


def create_test_case(n: int, key_length: int = KEY_LENGTH) -> list[tuple[bytes, bytes]]:
    return [(os.urandom(key_length), os.urandom(32)) for _ in range(n)]


def test_update() -> None:
    cases = create_test_case(10000)

    update_smt = asyncio.run(case_testing(cases))
    batch_smt = asyncio.run(case_testing_batch(cases))

    assert update_smt.root.hash == batch_smt.root.hash


async def case_testing(cases) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree(KEY_LENGTH)
    assert _smt.root.hash == EMPTY_HASH

    for k, v in cases:
        new_root = await _smt.update(k, v)
        assert _smt.root.hash == new_root.hash

    return _smt


async def case_testing_batch(cases) -> Coroutine[None, None, SparseMerkleTree]:
    _smt = SparseMerkleTree(KEY_LENGTH)
    assert _smt.root.hash == EMPTY_HASH

    new_root = await _smt.update(cases[:500], strict=True)
    assert _smt.root.hash == new_root.hash

    new_root = await _smt.update(cases[500:1500], strict=True)
    assert _smt.root.hash == new_root.hash

    new_root = await _smt.update(cases[1500:7000], strict=True)
    assert _smt.root.hash == new_root.hash

    new_root = await _smt.update(cases[7000:], strict=True)
    assert _smt.root.hash == new_root.hash

    return _smt
