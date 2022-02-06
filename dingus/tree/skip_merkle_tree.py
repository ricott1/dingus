from queue import Empty
from .constants import (
    DEFAULT_KEY_LENGTH,
    DEFAULT_SUBTREE_HEIGHT,
)
from .types import LeafNode, BranchNode, SubTree, EmptyNode, TreeNode
from .errors import *
from .utils import split_index, is_bit_set, split_keys_index
from typing import Coroutine, Any


from dingus.db import InMemoryDB, RocksDB


class SkipMerkleTree(object):
    def __init__(
        self,
        key_length: int = DEFAULT_KEY_LENGTH,
        subtree_height: int = DEFAULT_SUBTREE_HEIGHT,
        db: str = "inmemorydb",
    ) -> None:
        self.key_length = key_length
        self.subtree_height = subtree_height
        
        self.root = SubTree([0], [EmptyNode()])
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
            "update_subtree_calls": 0,
            "update_node_calls": 0,
        }

    async def print(
        self, subtree: SubTree, preamble: str = "    ", hash_length: int = 4
    ) -> str:
        BROWN = lambda t: f"\u001b[38;2;{105};{103};{60}m" + t + "\u001b[0m"
        head = f"R:{subtree.hash.hex()[:hash_length]}\n"
        body = []
        for i in reversed(range(len(subtree.nodes))):
            h, node = subtree.structure[i], subtree.nodes[i]
            if i < len(subtree.nodes) - 1:
                connector = "├"
            else:
                connector = "╰"
            if isinstance(node, EmptyNode):
                body.append(preamble + connector + "──" * h + f"─<∅{h}")

            elif isinstance(node, LeafNode):
                key = node.key[:4]
                bin_key = (
                    bin(int.from_bytes(key, "big"))
                    .lstrip("0b")
                    .zfill(8 * len(key))
                )
                
                body.append(preamble + connector + "──" * h + f"─<🌿{h}:{bin_key}:{node.hash.hex()[:hash_length]}")
            elif isinstance(node, BranchNode):

                right_node = await self.get_subtree(node.right_hash)
                left_node = await self.get_subtree(node.left_hash)
                left = await self.print(left_node, preamble + "    ")
                right = await self.print(right_node, preamble + f"{BROWN('│')}   ")
                _body = "\n".join(
                    [
                        f"{BROWN('─<B')}:{node.hash.hex()[:hash_length]}",
                        f"{preamble}{BROWN('├')}{right}",
                        f"{preamble}{BROWN('╰')}{left}",
                    ])
                    
                body.append(preamble + connector + "──" * h + _body)
        return head + "\n".join(body)

    async def get_subtree(self, node_hash: bytes) -> Coroutine[Any, Any, SubTree]:
        if node_hash == EmptyNode.hash:
            return SubTree([0], [EmptyNode()])

        data = await self._db.get(node_hash)
        self.stats["db_get"] += 1
        if not data:
            print("\nMISSING NODE")
            print(node_hash.hex())
            raise MissingNodeError

        structure, nodes = SubTree.parse(data, self.key_length)
        return SubTree(structure, nodes)

    async def set_subtree(self, subtree: SubTree) -> None:
        await self._db.set(subtree.hash, subtree.data)
        self.stats["db_set"] += 1

    async def write_to_db(self) -> None:
        # re batch in memory nodes and write subtrees to db
        await self._db.write()

    async def update(
        self,
        data: list[tuple[bytes, bytes]],
        strict: bool = False,
    ) -> Coroutine[Any, Any, SubTree]:
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """
        if len(data) == 0:
            return self.root

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

        self.root = await self._update_subtree(keys, values, self.root, 0)
        await self.write_to_db()
        return self.root

    async def _update_subtree(
        self,
        keys: list[bytes],
        values: list[bytes],
        current_subtree: SubTree,
        height: int,
    ) -> Coroutine[Any, Any, SubTree]:

        self.stats["update_subtree_calls"] += 1
        assert len(keys) == len(values)
        assert (height%self.subtree_height) == 0
        if len(keys) == 0:
            return current_subtree

        await self._db.delete(current_subtree.hash)
        self.stats["db_delete"] += 1

        new_nodes = []
        new_structure = []
        V = 0
        print("\nUPDATING SKIP", len(keys))
        # print(current_subtree)
        for i in range(len(current_subtree.nodes)):
            h = current_subtree.structure[i]
            current_node = current_subtree.nodes[i]
            print("\nCURRENT BIN",h, V, V + (2 << (self.subtree_height - h)))
            print(current_node.hash.hex()[:4])
            # The following only works for the default value DEFAULT_SUBTREE_HEIGHT = 8
            bin_idx = split_keys_index(
                keys, height // 8, V + (2 << (self.subtree_height - h))
            )
            
            print(f"BIN IDX: {bin_idx}")
            print([k[height // 8] for k in keys])
            bin_keys, keys = keys[:bin_idx], keys[bin_idx:]
            bin_values, values = values[:bin_idx], values[bin_idx:]
            print([k[height // 8] for k in keys])

            _nodes, _heights = await self._update_node(
                bin_keys, bin_values, current_node, height + h
            )
            new_nodes += _nodes
            new_structure += _heights
            V += (2 << (self.subtree_height - h))

        new_structure = [h% self.subtree_height for h in new_structure]
        assert V == (2 << self.subtree_height)
        # print(f"nodes : {new_nodes} {new_structure}")
        # assert len(new_structure) == len(new_nodes)
        # assert len(new_structure) <= 2<<self.subtree_height
        new_subtree = SubTree(new_structure, new_nodes)
        # print(f"\nnew_subtree {height} : {new_subtree.hash.hex()}")
        await self.set_subtree(new_subtree)
        return new_subtree

    async def _update_node(
        self,
        keys: list[bytes],
        values: list[bytes],
        current_node: TreeNode,
        height: int,
    ) -> Coroutine[Any, Any, tuple[list[TreeNode], list[int]]]:
        assert height < 8 * self.key_length
        assert len(keys) == len(values)
        self.stats["update_node_calls"] += 1
        if len(keys) == 0:
            return ([current_node], [height])
        
        if isinstance(current_node, EmptyNode) and len(keys) == 1:
            new_leaf = LeafNode(keys[0], values[0])
            self.stats["leaf_created"] += 1
            return ([new_leaf], [height])

        #If we are at the bottom of the tree, we call update_subtree and return update nodes
        if (height % self.subtree_height) == self.subtree_height - 1:
            if isinstance(current_node, EmptyNode):
                left_subtree = await self.get_subtree(EmptyNode.hash)
                right_subtree = await self.get_subtree(EmptyNode.hash)
            elif isinstance(current_node, LeafNode):
                if is_bit_set(current_node.key, height):
                    left_subtree = SubTree([0], [EmptyNode()])
                    right_subtree = SubTree([0], [current_node])
                    await self.set_subtree(right_subtree)
                else:
                    left_subtree = SubTree([0], [current_node])
                    await self.set_subtree(left_subtree)
                    right_subtree = SubTree([0], [EmptyNode()])
            elif isinstance(current_node, BranchNode):
                # Branch node can only be stored at bottom of subtree
                left_subtree = await self.get_subtree(current_node.left_hash)
                right_subtree = await self.get_subtree(current_node.right_hash)

            idx = split_index(keys, lambda k: is_bit_set(k, height))

            left_subtree = await self._update_subtree(
                keys[:idx], values[:idx], left_subtree, height + 1
            )
            right_subtree = await self._update_subtree(
                keys[idx:], values[idx:], right_subtree, height + 1
            )
            current_node = BranchNode(left_subtree.hash, right_subtree.hash)

            return ([current_node], [self.subtree_height - 1])

        
        #Else, we just call _update_node and return the returned values
        if isinstance(current_node, EmptyNode):
            left_node = EmptyNode()
            right_node = EmptyNode()
        elif isinstance(current_node, LeafNode):
            print("UPDATING LEAF", current_node.hash.hex()[:4], height, is_bit_set(current_node.key, height))
            if is_bit_set(current_node.key, height):
                left_node = EmptyNode()
                right_node = current_node
            else:
                left_node = current_node
                right_node = EmptyNode()
        elif isinstance(current_node, BranchNode):
            assert 1==2

        idx = split_index(keys, lambda k: is_bit_set(k, height))

        left_nodes, left_heights = await self._update_node(
            keys[:idx], values[:idx], left_node, height + 1
        )
        right_nodes, right_heights = await self._update_node(
            keys[idx:], values[idx:], right_node, height + 1
        )



        return (left_nodes + right_nodes, left_heights + right_heights)
