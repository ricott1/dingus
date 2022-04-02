from typing import Coroutine
from dingus.tree.sparse_merkle_tree import SparseMerkleTree
from dingus.tree.skip_merkle_tree import SkipMerkleTree
from dingus.tree.constants import EMPTY_HASH
import asyncio
from tests.tree.utils import create_test_case

KEY_LENGTH = 32


def test_update_smt() -> None:
    keys, values = create_test_case(10000)

    update_smt = asyncio.run(case_testing(SparseMerkleTree(KEY_LENGTH), keys, values))
    batch_smt = asyncio.run(case_testing_batch(SparseMerkleTree(KEY_LENGTH), keys, values))

    assert update_smt == batch_smt 


def test_update_skmt() -> None:
    keys, values = create_test_case(10000)

    update_skmt = asyncio.run(case_testing(SkipMerkleTree(KEY_LENGTH), keys, values))
    batch_skmt = asyncio.run(case_testing_batch(SkipMerkleTree(KEY_LENGTH), keys, values))

    assert update_skmt == batch_skmt


async def case_testing(tree, keys, values) -> Coroutine[None, None, SparseMerkleTree]:
    assert tree.root.hash == tree.hasher.empty

    new_root = await tree.update(keys, values)
    assert tree.root.hash == new_root.hash

    return tree.root.hash


async def case_testing_batch(tree, keys, values) -> Coroutine[None, None, SparseMerkleTree]:
    assert tree.root.hash == tree.hasher.empty

    new_root = await tree.update(keys[:500], values[:500])
    assert tree.root.hash == new_root.hash

    new_root = await tree.update(keys[500:1500], values[500:1500])
    assert tree.root.hash == new_root.hash

    new_root = await tree.update(keys[1500:7000], values[1500:7000])
    assert tree.root.hash == new_root.hash

    new_root = await tree.update(keys[7000:], values[7000:])
    assert tree.root.hash == new_root.hash

    return tree.root.hash
