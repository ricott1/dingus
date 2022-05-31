from typing import Coroutine
from dingus.tree.skip_merkle_tree import SkipMerkleTree
from dingus.tree.constants import EMPTY_HASH
import time
import random
import asyncio
import os
from dingus.utils import hash

KEY_LENGTH = 4
IDX_LENGTH = 3


def test_large_update(capsys) -> None:
    start_time = time.time()
    n_trs = 200
    events_per_trs = 50
    extra_topic_per_event = 3

    event_idx = 0
    event_keys = []
    for _ in range(n_trs):
        trs_id = os.urandom(KEY_LENGTH)

        for _ in range(events_per_trs):
            local_idx = 0
            idx = (4*event_idx + local_idx).to_bytes(IDX_LENGTH, "big")
            event_keys.append(trs_id + idx)
            for _ in range(extra_topic_per_event):
                local_idx += 1
                idx = (4*event_idx + local_idx).to_bytes(IDX_LENGTH, "big")
                event_keys.append(os.urandom(KEY_LENGTH) + idx)

            event_idx += 1

    values = [hash(k) for k in event_keys]
    print(values)

    with capsys.disabled():
        print(f"\ncreate test cases: {time.time() - start_time:.2f}s")
    asyncio.run(
        case_testing_batch(event_keys, values, capsys)
    )


async def case_testing_batch(keys, values, capsys) -> Coroutine[None, None, SkipMerkleTree]:
    _smt = SkipMerkleTree(KEY_LENGTH + 4)
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _smt.update(keys, values)
    assert _smt.root.hash == new_root.hash
    with capsys.disabled():
        print(
            f"create tree with {len(keys)} leaves: {time.time() - start_time:.2f}s"
        )
        print(_smt.stats)

    return _smt