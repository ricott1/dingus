from .constants import DEFAULT_KEY_LENGTH, SUBTREE_PREFIX, DEFAULT_SUBTREE_HEIGHT
from .types import LeafNode, BranchNode, SubTree, EmptyNode, TreeNode
from .errors import *
from .utils import split_index, is_bit_set
from typing import Coroutine, Any
import asyncio

from dingus.db import InMemoryDB, RocksDB


class SkipMerkleTree(object):
    def __init__(self, key_length: int = DEFAULT_KEY_LENGTH, subtree_height: int = DEFAULT_SUBTREE_HEIGHT, db: str = "rocksdb") -> None:
        self.key_length = key_length
        self.subtree_height = subtree_height
        self.subtree_nodes = 2**(self.subtree_height - 1)
        self.root_hash = EmptyNode.hash
        if db == "inmemorydb":
            self._db = InMemoryDB()
        elif db == "rocksdb":
            self._db = RocksDB()

    async def print(self, node: TreeNode, preamble: str = "    ", hash_length: int = 4) -> str:
        BROWN = lambda t: f"\u001b[38;2;{105};{103};{60}m" + t + "\u001b[0m"
        if isinstance(node, EmptyNode):
            return "∅"
        
        if isinstance(node, LeafNode):
            bin_key = bin(int.from_bytes(node.key, "big")).lstrip("0b").zfill(8*len(node.key))
            return f"─<🌿{bin_key}:{node.hash.hex()[:hash_length]}"
                
        right_node = await self.get_node(node.right_hash)
        left_node = await self.get_node(node.left_hash)
        left = await self.print(left_node, preamble + "    ")
        right = await self.print(right_node, preamble + f"{BROWN('│')}   ")
        return "\n".join([
            f"{BROWN('─<B')}:{node.hash.hex()[:hash_length]}",
            f"{preamble}{BROWN('├')}{right}",
            f"{preamble}{BROWN('╰')}{left}"
        ])

    # async def _get_node(self, node_hash: bytes) -> Coroutine[Any, Any, TreeNode]: #Deprecated
    #     if node_hash == EmptyNode.hash:
    #         return EmptyNode()
        
    #     data = await self._db.get(node_hash)

    #     if not data:
    #         raise MissingNodeError

    #     if data.startswith(LEAF_PREFIX):
    #         key, value = LeafNode.parse(data, self.key_length)
    #         return LeafNode(key, value)

    #     left_hash, right_hash = BranchNode.parse(data)
    #     return BranchNode(left_hash, right_hash)
    
    async def get_subtree(self, node_hash: bytes) -> Coroutine[Any, Any, SubTree]:
        if node_hash == EmptyNode.hash:
            return SubTree([0]*self.subtree_nodes, [])
        
        data = await self._db.get(node_hash)
        if not data:
            raise MissingNodeError
        if not data.startswith(SUBTREE_PREFIX):
            raise InvalidDataError

        structure, nodes = SubTree.parse(data, self.key_length)
        return SubTree(structure, nodes)
        
    async def set_node(self, node: TreeNode) -> None:
        await self._db.set(node.hash, node.data)
    
    async def write_to_db(self) -> None:
        # re batch in memory nodes and write subtrees to db
        await self._db.write()

    async def update(self, key: bytes, value: bytes, starting_height: int = 0) -> Coroutine[Any, Any, TreeNode]: 
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
    
    async def _update(self, key: bytes, value: bytes, current_node: TreeNode, height: int) -> Coroutine[Any, Any, TreeNode]:
        new_leaf = LeafNode(key, value)
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
                # Append defaultBranch to ancestor_nodes
                ancestor_nodes.append(new_branch)
                h += 1 
            # Create last branch node, parent of node and new_leaf

            if is_bit_set(key, h):
                bottom_node = BranchNode(current_node.hash, new_leaf.hash)
            else:
                bottom_node = BranchNode(new_leaf.hash, current_node.hash)
            await self.set_node(bottom_node)

        # Finally update all branch nodes in ancestor_nodes
        # Starting from the last
        assert len(ancestor_nodes) == h - height
        while h > height:
            p = ancestor_nodes.pop()
            await self._db.delete(p.hash)
            h -= 1
            if is_bit_set(key, h):
                p.right_hash = bottom_node.hash
            else:
                p.left_hash = bottom_node.hash
            
            await self.set_node(p)
            bottom_node = p

        return bottom_node
        

    async def update_batch(self, data: list[tuple[bytes, bytes]], strict: bool = False, starting_height: int = 0) -> Coroutine[Any, Any, bytes]: 
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
            
        sorted_data = sorted(data, key = lambda d: d[0])
        keys = []
        values = []
        for key, value in sorted_data:
            keys.append(key)
            values.append(value)
        
        current_root = self.get_subtree(self.root_hash)
        new_root = await self._update_batch(keys, values, current_root, starting_height)
        await self.write_to_db()
        return new_root.hash

    def skip_to_bottom(self, keys: list[bytes], values: list[bytes], current_subtree: SubTree, height: int) -> TreeNode:
        # If len(keys) == 0, return current subtree

        # If len(keys) == 1, 
        
        # Split keys into bins, one for each bottom leaf, self.subtree_nodes in total

        # Find relevant node in subtree for each bin

        # If node is at the bottom (structure[i] == subtree_height) and it is a branch, we can call recursively _update_batch by getting the subtree from that node child

        # Else, we call update subtree routine. 
            # We complete subtree, and when height reached height + subtree_height, we need to create a new subtree
            # IDEA: call same subroutine and check at the end whther to construct and store the subtree depending if height%subtree_height == 0
            # how do you reconstruct the tree? need all nodes in subtree and their height

        # Else, we are going to create a new branch. Depending on the height, this new branch will be in the same subtree or in a new one
        
    async def _update_batch(self, keys: list[bytes], values: list[bytes], current_subtree: SubTree, height: int) -> Coroutine[Any, Any, bytes]: 
        assert height < 8 * self.key_length
        assert len(keys) == len(values)
        
        if len(keys) == 0:
            return current_subtree

        if len(keys) == 1 and isinstance(current_subtree, EmptyNode):
            new_leaf = LeafNode(keys[0], values[0])
            await self.set_node(new_leaf)
            return new_leaf

        
        bins = [[(key, value) for key, value in zip(keys, values) if key[height] == bin] for bin in range(256)]
        for h in range(self.subtree_height - 1):
            _bins = []
            for bin in bins:
                _keys, _values = bin
                idx = split_index(_keys, lambda k: is_bit_set(k, height + h)) 
                _bins += [(_keys[:idx], _values[:idx]), (_keys[idx:], _values[idx:])]
            bins = list(_bins)
        
        assert len(bins) == len(current_subtree.structure) == len(current_subtree.nodes)

        for h, node, bin in zip(current_subtree.structure, current_subtree.nodes, bins):
            if isinstance(current_subtree, BranchNode): 
                assert h == self.subtree_height
                left_subtree = await self.get_subtree(current_subtree.left_hash)
                right_subtree = await self.get_subtree(current_subtree.right_hash)
                await self._db.delete(current_subtree.hash)
                left_subtree = await self._update_batch(bin[0], bin[1], left_subtree, height + 1)
                right_subtree = await self._update_batch(bin[0], bin[1], right_subtree, height + 1)

                new_root_hash - SubTree

                current_subtree = SubTree(new_structure, new_nodes)
                await self.set_node(current_subtree)
                return current_subtree



        if isinstance(current_node, LeafNode):
            if is_bit_set(current_node.key, height):
                left_node = EmptyNode()
                right_node = current_node
            else:
                left_node = current_node
                right_node = EmptyNode()
        elif isinstance(current_node, EmptyNode):
            left_node = EmptyNode()
            right_node = EmptyNode()
        elif isinstance(current_node, BranchNode): 
            left_node = await self.get_node(current_node.left_hash)
            right_node = await self.get_node(current_node.right_hash)
            await self._db.delete(current_node.hash)
        
        
            

        concurrent_update = (height < 2) and (0 < idx < len(keys))
        if concurrent_update:
            left_node, right_node = await asyncio.gather(
                self._update_batch(keys[:idx], values[:idx], left_node, height + 1),
                self._update_batch(keys[idx:], values[idx:], right_node, height + 1)
            )
        else:
            left_node = await self._update_batch(keys[:idx], values[:idx], left_node, height + 1)
            right_node = await self._update_batch(keys[idx:], values[idx:], right_node, height + 1)

        current_node = BranchNode(left_node.hash, right_node.hash)
        await self.set_node(current_node)
        return current_node

    async def remove(self, key: bytes) -> Coroutine[Any, Any, TreeNode]: 
        if len(key) != self.key_length:
            raise InvalidKeyError

        ancestor_nodes: list[BranchNode] = []
        current_node = self.root
        h = 0
        current_node_sibling: TreeNode =  EmptyNode()

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
            bottom_node = current_node_sibling

            h -= 1
            # In order to move sibling up the tree
            # an exact emptyHash check is required
            # not using EMPTY_HASH here to make sure we use correct hash from Empty class
            while h > 0:
                p = ancestor_nodes[h - 1]

                # if one of the children is empty then break the condition
                if p.left_hash != EmptyNode.hash and p.right_hash!= EmptyNode.hash:
                    break

                await self._db.delete(p.hash)
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
