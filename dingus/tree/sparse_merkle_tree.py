from .constants import (
    BRANCH_PREFIX,
    DEFAULT_KEY_LENGTH,
    LEAF_PREFIX,
)
from .types import LeafNode, BranchNode, EmptyNode, TreeNode
from .utils import split_index, is_bit_set
from .errors import *
from typing import Coroutine, Any
import asyncio

from dingus.db import InMemoryDB, RocksDB


class SparseMerkleTree(object):
    def __init__(
        self, key_length: int = DEFAULT_KEY_LENGTH, db: str = "inmemorydb"
    ) -> None:
        self.key_length = key_length
        self.root = EmptyNode()
        if db == "inmemorydb":
            self._db = InMemoryDB()
        elif db == "rocksdb":
            self._db = RocksDB()
        self.stats = {
            "db_set": 0,
            "db_get": 0,
            "db_delete": 0,
            "hashes": 0,
            "leaf_created": 0,
            "branch_created": 0,
            "update_calls": 0,
        }

    async def print(
        self, node: TreeNode, preamble: str = "    ", hash_length: int = 4
    ) -> str:
        BROWN = lambda t: f"\u001b[38;2;{105};{103};{60}m" + t + "\u001b[0m"
        if isinstance(node, EmptyNode):
            return "∅"

        if isinstance(node, LeafNode):
            key = node.key[:4]
            bin_key = (
                bin(int.from_bytes(key, "big"))
                .lstrip("0b")
                .zfill(8 * len(key))
            )
            return f"─<🌿{bin_key}:{node.hash.hex()[:hash_length]}"

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

    async def update(
        self, key: bytes, value: bytes, starting_height: int = 0
    ) -> Coroutine[Any, Any, TreeNode]:
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """

        if len(value) == 0:
            raise EmptyValueError

        if len(key) != self.key_length:
            raise InvalidKeyError

        self.root = await self._update(key, value, self.root, starting_height)
        await self.write_to_db()
        return self.root

    async def _update(
        self, key: bytes, value: bytes, current_node: TreeNode, height: int
    ) -> Coroutine[Any, Any, TreeNode]:
        self.stats["update_calls"] += 1
        new_leaf = LeafNode(key, value)
        self.stats["leaf_created"] += 1
        await self.set_node(new_leaf)

        # if the current_node is EMPTY node then assign it to leaf node and return
        if isinstance(current_node, EmptyNode):
            return new_leaf

        h = height
        ancestor_nodes: list[BranchNode] = []
        while isinstance(current_node, BranchNode):
            ancestor_nodes.append(current_node)
            if is_bit_set(key, h):
                current_node = await self.get_node(current_node.right_hash)
            else:
                current_node = await self.get_node(current_node.left_hash)
            h += 1

        # The current_node is an empty node, new_leaf will replace the default empty node or current_node will be updated to new_leaf
        if isinstance(current_node, EmptyNode):
            # delete the empty node and update the tree, the new leaf will substitute the empty node
            bottom_node = new_leaf
        elif current_node.key == key:
            bottom_node = new_leaf
        else:
            # We need to create BranchNodees in the tree to fulfill the
            # Condition of one leaf per empty subtree
            # Note: h is set to the last value from the previous loop

            while is_bit_set(key, h) == is_bit_set(current_node.key, h):
                # Create branch node with empty value
                new_branch = BranchNode(EmptyNode.hash, EmptyNode.hash)
                self.stats["branch_created"] += 1
                # Append defaultBranch to ancestor_nodes
                ancestor_nodes.append(new_branch)
                h += 1
            # Create last branch node, parent of node and new_leaf

            if is_bit_set(key, h):
                bottom_node = BranchNode(current_node.hash, new_leaf.hash)
            else:
                bottom_node = BranchNode(new_leaf.hash, current_node.hash)
            self.stats["branch_created"] += 1
            await self.set_node(bottom_node)

        # Finally update all branch nodes in ancestor_nodes
        # Starting from the last
        assert len(ancestor_nodes) == h - height
        while h > height:
            p = ancestor_nodes.pop()
            await self._db.delete(p.hash)
            self.stats["db_delete"] += 1
            h -= 1
            if is_bit_set(key, h):
                p.right_hash = bottom_node.hash
            else:
                p.left_hash = bottom_node.hash

            await self.set_node(p)
            bottom_node = p

        return bottom_node

    async def update_batch(
        self,
        data: list[tuple[bytes, bytes]],
        strict: bool = False,
        starting_height: int = 0,
    ) -> Coroutine[Any, Any, TreeNode]:
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """
        if len(data) == 0:
            return self.root
        if len(data) == 1:
            return await self.update(*data[0])

        if strict:
            keys_set = {}
            for key, value in data:
                if len(value) == 0:
                    raise EmptyValueError

                if len(key) != self.key_length:
                    raise InvalidKeyError

                if key in keys_set:
                    raise InvalidKeyError
                keys_set[key] = True

        sorted_data = sorted(data, key=lambda d: d[0])
        keys = []
        values = []
        for key, value in sorted_data:
            keys.append(key)
            values.append(value)
        self.root = await self._update_batch(keys, values, self.root, starting_height)
        await self.write_to_db()
        return self.root

    async def _update_batch(
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

        # if len(keys) == 1:
        #     return await self._update(keys[0], values[0], current_node, height)

        # if len(keys) == 1 and isinstance(current_node, EmptyNode):
        #     new_leaf = LeafNode(keys[0], values[0])
        #     await self.set_node(new_leaf)
        #     return new_leaf
        if isinstance(current_node, EmptyNode):
            if len(keys) == 1:
                new_leaf = LeafNode(keys[0], values[0])
                self.stats["leaf_created"] += 1
                await self.set_node(new_leaf)
                return new_leaf
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
        #         self._update_batch(keys[:idx], values[:idx], left_node, height + 1),
        #         self._update_batch(keys[idx:], values[idx:], right_node, height + 1),
        #     )
        # else:
        left_node = await self._update_batch(
            keys[:idx], values[:idx], left_node, height + 1
        )
        right_node = await self._update_batch(
            keys[idx:], values[idx:], right_node, height + 1
        )

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
