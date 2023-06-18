from .constants import BRANCH_PREFIX, DEFAULT_KEY_LENGTH, EMPTY_HASH, LEAF_PREFIX, DEFAULT_HASHER
from .types import LeafNode, BranchNode, EmptyNode, TreeNode
from .utils import split_index, is_bit_set
from .errors import *
from typing import Coroutine, Any
import os
from dingus.crypto import hash

from dingus.db import InMemoryDB, RocksDB


class SparseMerkleTree(object):
    def __init__(self, key_length: int = DEFAULT_KEY_LENGTH, db: str = "inmemorydb") -> None:
        self.key_length = key_length
        self.root = EmptyNode()
        if db == "inmemorydb":
            self._db = InMemoryDB()
        elif db == "rocksdb":
            self._db = RocksDB(filename="./database/smt.db")
        self.stats = {
            "db_set": 0,
            "db_get": 0,
            "db_delete": 0,
            "hashes": 0,
            "leaf_created": 0,
            "branch_created": 0,
            "update_calls": 0,
        }

    async def print(self, node: TreeNode, preamble: str = "    ", hash_length: int = 4) -> str:
        BROWN = lambda t: f"\u001b[38;2;{105};{103};{60}m" + t + "\u001b[0m"
        if isinstance(node, EmptyNode):
            return "∅"

        if isinstance(node, LeafNode):
            key = node.key[:2]
            bin_key = bin(int.from_bytes(key, "big")).lstrip("0b").zfill(8 * len(key))
            return f"─<🌿{key.hex()}:{node.hash.hex()[:hash_length]}"

        right_node = await self.get_node(node.right_hash)
        left_node = await self.get_node(node.left_hash)
        left = await self.print(left_node, preamble + "    ")
        right = await self.print(right_node, preamble + f"{BROWN('│')}   ")
        return "\n".join(
            [
                f"{BROWN('─<B')}:{node.hash.hex()[:hash_length]}",
                f"{preamble}{BROWN('├')}{right}",
                f"{preamble}{BROWN('╰')}{left}",
            ]
        )

    async def get_node(self, node_hash: bytes) -> Coroutine[Any, Any, TreeNode]:
        if node_hash == EmptyNode.hash:
            return EmptyNode()

        data = await self._db.get(node_hash)
        self.stats["db_get"] += 1

        if not data:
            raise MissingNodeError

        if data.startswith(LEAF_PREFIX):
            key, value = LeafNode.parse(data, self.key_length)
            self.stats["leaf_created"] += 1
            return LeafNode(key, value)

        if data.startswith(BRANCH_PREFIX):
            left_hash, right_hash = BranchNode.parse(data)
            self.stats["branch_created"] += 1
            return BranchNode(left_hash, right_hash)

        raise InvalidDataError

    async def set_node(self, node: TreeNode) -> None:
        await self._db.set(node.hash, node.data)
        self.stats["db_set"] += 1

    async def write_to_db(self) -> None:
        await self._db.write()

    # async def update(
    #     self, key: bytes, value: bytes, starting_height: int = 0
    # ) -> Coroutine[Any, Any, TreeNode]:
    #     """
    #     As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
    #     """

    #     if len(value) == 0:
    #         raise EmptyValueError

    #     if len(key) != self.key_length:
    #         raise InvalidKeyError

    #     self.root = await self._update(key, value, self.root, starting_height)
    #     await self.write_to_db()
    #     return self.root

    # async def _update(
    #     self, key: bytes, value: bytes, current_node: TreeNode, height: int
    # ) -> Coroutine[Any, Any, TreeNode]:
    #     self.stats["update_calls"] += 1
    #     new_leaf = LeafNode(key, value)
    #     self.stats["leaf_created"] += 1
    #     await self.set_node(new_leaf)

    #     # if the current_node is EMPTY node then assign it to leaf node and return
    #     if isinstance(current_node, EmptyNode):
    #         return new_leaf

    #     h = height
    #     ancestor_nodes: list[BranchNode] = []
    #     while isinstance(current_node, BranchNode):
    #         ancestor_nodes.append(current_node)
    #         if is_bit_set(key, h):
    #             current_node = await self.get_node(current_node.right_hash)
    #         else:
    #             current_node = await self.get_node(current_node.left_hash)
    #         h += 1

    #     # The current_node is an empty node, new_leaf will replace the default empty node or current_node will be updated to new_leaf
    #     if isinstance(current_node, EmptyNode):
    #         # delete the empty node and update the tree, the new leaf will substitute the empty node
    #         bottom_node = new_leaf
    #     elif current_node.key == key:
    #         bottom_node = new_leaf
    #     else:
    #         # We need to create BranchNodees in the tree to fulfill the
    #         # Condition of one leaf per empty subtree
    #         # Note: h is set to the last value from the previous loop

    #         while is_bit_set(key, h) == is_bit_set(current_node.key, h):
    #             # Create branch node with empty value
    #             new_branch = BranchNode(EmptyNode.hash, EmptyNode.hash)
    #             self.stats["branch_created"] += 1
    #             # Append defaultBranch to ancestor_nodes
    #             ancestor_nodes.append(new_branch)
    #             h += 1
    #         # Create last branch node, parent of node and new_leaf

    #         if is_bit_set(key, h):
    #             bottom_node = BranchNode(current_node.hash, new_leaf.hash)
    #         else:
    #             bottom_node = BranchNode(new_leaf.hash, current_node.hash)
    #         self.stats["branch_created"] += 1
    #         await self.set_node(bottom_node)

    #     # Finally update all branch nodes in ancestor_nodes
    #     # Starting from the last
    #     assert len(ancestor_nodes) == h - height
    #     while h > height:
    #         p = ancestor_nodes.pop()
    #         await self._db.delete(p.hash)
    #         self.stats["db_delete"] += 1
    #         h -= 1
    #         if is_bit_set(key, h):
    #             p.right_hash = bottom_node.hash
    #         else:
    #             p.left_hash = bottom_node.hash

    #         await self.set_node(p)
    #         bottom_node = p

    #     return bottom_node

    async def update(
        self,
        keys: list[bytes],
        values: list[bytes],
    ) -> Coroutine[Any, Any, TreeNode]:
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """
        if len(keys) == 0:
            return self.root

        sorted_data = sorted(zip(keys, values), key=lambda d: d[0])
        keys = [key for key, _ in sorted_data]
        values = [value for _, value in sorted_data]

        self.root = await self._update(keys, values, self.root, 0)
        await self.write_to_db()
        return self.root

    async def _update(
        self,
        keys: list[bytes],
        values: list[bytes],
        current_node: TreeNode,
        height: int,
    ) -> Coroutine[Any, Any, TreeNode]:
        self.stats["update_calls"] += 1
        assert height < 8 * self.key_length
        assert len(keys) == len(values)

        if len(keys) == 0:
            return current_node

        if len(keys) == 1:
            if isinstance(current_node, EmptyNode):
                new_leaf = LeafNode(keys[0], values[0])
                self.stats["leaf_created"] += 1
                await self.set_node(new_leaf)
                return new_leaf
            elif isinstance(current_node, LeafNode) and current_node.key == keys[0]:
                await self._db.delete(current_node.hash)
                self.stats["db_delete"] += 1
                new_leaf = LeafNode(keys[0], values[0])
                self.stats["leaf_created"] += 1
                await self.set_node(new_leaf)
                return new_leaf

        if isinstance(current_node, EmptyNode):
            left_node = EmptyNode()
            right_node = EmptyNode()
        elif isinstance(current_node, LeafNode):
            if is_bit_set(current_node.key, height):
                left_node = EmptyNode()
                right_node = current_node
            else:
                left_node = current_node
                right_node = EmptyNode()
        elif isinstance(current_node, BranchNode):
            left_node = await self.get_node(current_node.left_hash)
            right_node = await self.get_node(current_node.right_hash)
            await self._db.delete(current_node.hash)
            self.stats["db_delete"] += 1

        idx = split_index(keys, lambda k: is_bit_set(k, height))

        # concurrent_update = (height < 8) and (0 < idx < len(keys))
        # if concurrent_update:
        #     left_node, right_node = await asyncio.gather(
        #         self._update(keys[:idx], values[:idx], left_node, height + 1),
        #         self._update(keys[idx:], values[idx:], right_node, height + 1),
        #     )
        # else:
        left_node = await self._update(keys[:idx], values[:idx], left_node, height + 1)
        right_node = await self._update(keys[idx:], values[idx:], right_node, height + 1)

        current_node = BranchNode(left_node.hash, right_node.hash)
        self.stats["branch_created"] += 1
        await self.set_node(current_node)
        return current_node

    async def remove(self, key: bytes) -> Coroutine[Any, Any, TreeNode]:
        if len(key) != self.key_length:
            raise InvalidKeyError

        ancestor_nodes: list[BranchNode] = []
        current_node = self.root
        h = 0
        current_node_sibling: TreeNode = EmptyNode()

        # Collect all ancestor nodes through traversing the binary expansion by height
        # End of the loop ancestor_nodes has all the branch nodes
        # current_node will be the leaf/node we are looking to remove
        while isinstance(current_node, BranchNode):
            ancestor_nodes.append(current_node)
            if is_bit_set(key, h):
                current_node_sibling = await self.get_node(current_node.left_hash)
                current_node = await self.get_node(current_node.right_hash)
            else:
                current_node_sibling = await self.get_node(current_node.right_hash)
                current_node = await self.get_node(current_node.left_hash)
            h += 1

        # When current_node is empty, nothing to remove
        if isinstance(current_node, EmptyNode):
            return current_node

        # When the input key does not match node key, nothing to remove
        if current_node.key != key:
            return current_node

        bottom_node = EmptyNode()

        # current_node has a branch sibling, delete current_node
        if isinstance(current_node_sibling, BranchNode):
            await self._db.delete(current_node.hash)
        elif isinstance(current_node_sibling, LeafNode):
            # current_node has a leaf sibling,
            # remove the leaf and move sibling up the tree
            await self._db.delete(current_node.hash)
            self.stats["db_delete"] += 1
            bottom_node = current_node_sibling

            h -= 1
            # In order to move sibling up the tree
            # an exact emptyHash check is required
            # not using EMPTY_HASH here to make sure we use correct hash from Empty class
            while h > 0:
                p = ancestor_nodes[h - 1]

                # if one of the children is empty then break the condition
                if p.left_hash != EmptyNode.hash and p.right_hash != EmptyNode.hash:
                    break

                await self._db.delete(p.hash)
                self.stats["db_delete"] += 1
                h -= 1

        # finally update all branch nodes in ancestor_nodes.
        # note that h now is set to the correct height from which
        # nodes have to be updated
        while h > 0:
            p = ancestor_nodes[h - 1]
            h -= 1

            if is_bit_set(key, h):
                p.right_hash = bottom_node.hash
            else:
                p.left_hash = bottom_node.hash

            await self.set_node(p)
            bottom_node = p

        self.root = bottom_node
        return bottom_node

def create_test_case(n: int, key_length: int = 2) -> list[tuple[bytes, bytes]]:
    keys = sorted([hash(i.to_bytes(2))[:key_length] for i in range(n)])
    for i in range(len(keys)):
        print(keys[i].hex())
        keys[i] = (keys[i][0] & 0x7F).to_bytes(1) + b"".join([b.to_bytes(1) for b in keys[i][1:]])
        print(keys[i].hex())

    values = [hash(k) for k in keys]

    return (keys, values)
    
async def testing():
    import time
    initial_keys, initial_values = create_test_case(8)
    _smt = SparseMerkleTree(2)
    assert _smt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _smt.update(initial_keys, initial_values)
    assert _smt.root.hash == new_root.hash
    print(f"create SMT tree with {len(initial_keys)} leaves: {time.time() - start_time:.2f}s")
    from .skip_merkle_tree import SkipMerkleTree, verify, binary_expansion
    _skmt = SkipMerkleTree(2)
    assert _skmt.root.hash == EMPTY_HASH
    start_time = time.time()
    new_root = await _skmt.update(initial_keys, initial_values)
    assert _skmt.root.hash == new_root.hash == _smt.root.hash
    print(await _smt.print(_smt.root))


    query_keys = initial_keys[4:6]
    proof = await _skmt.generate_proof(query_keys)
    for sh in proof.sibling_hashes:
        print(sh.hex())
    for q in proof.queries:
        print(f"query: {q.key.hex()}:{q.value.hex()[:4]} bm:{q.binary_bitmap}=={q.bitmap.hex()}")
    
    proof.queries[0].bitmap = b"\x16\x00" 
    proof.queries[0].binary_bitmap = binary_expansion(proof.queries[0].bitmap).lstrip("0")
    for q in proof.queries:
        print(f"query: {q.key.hex()}:{q.value.hex()[:4]} bm:{q.binary_bitmap}=={q.bitmap.hex()}")

    check = verify(query_keys, proof, _skmt.root.hash, 2)
    assert check
    print(f"verify proof: {check}")
    return _smt
if __name__ == "__main__":
    import asyncio
    asyncio.run(testing())