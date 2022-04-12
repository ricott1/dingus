from itertools import accumulate
from operator import le

from numpy import isin
from .hasher import TreeHasher, ECCHasher
from .constants import (
    DEFAULT_KEY_LENGTH,
    DEFAULT_SUBTREE_MAX_HEIGHT,
    DEFAULT_HASHER
)
from .types import LeafNode, SubTree, EmptyNode, TreeNode, StubNode
from .errors import *
from .utils import is_bit_set
from typing import Coroutine, Any


from dingus.db import InMemoryDB, RocksDB


class SkipMerkleTree(object):
    def __init__(
        self,
        key_length: int = DEFAULT_KEY_LENGTH,
        subtree_height: int = DEFAULT_SUBTREE_MAX_HEIGHT,
        db: str = "inmemorydb",
        hasher = DEFAULT_HASHER
    ) -> None:
        self.key_length = key_length
        self.subtree_height = subtree_height
        self.max_number_of_nodes = 1 << self.subtree_height
        if hasher == "tree":
            self.hasher = TreeHasher()
        elif hasher == "ecc":
            self.hasher = ECCHasher()
        else:
            self.hasher = TreeHasher()

        self.root = SubTree([0], [EmptyNode()], self.hasher)
        if db == "inmemorydb":
            self._db = InMemoryDB()
        elif db == "rocksdb":
            self._db = RocksDB(filename="./database/skmt.db")
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
            if i > 0:
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
            elif isinstance(node, StubNode):
                current_subtree = await self.get_subtree(node.hash)
                # right_node = await self.get_subtree(node.right_hash)
                # left_node = await self.get_subtree(node.left_hash)
                # left = await self.print(left_node, preamble + "    ")
                # right = await self.print(right_node, preamble + f"{BROWN('│')}   ")
                ctp = await self.print(current_subtree, preamble + "    ")
                _body = "\n".join(
                    [
                        f"{BROWN('─<B')}:{node.hash.hex()[:hash_length]}",
                        f"{preamble}{BROWN('├')}{ctp}",
                    ])
                    
                body.append(preamble + connector + "──" * h + _body)
        return head + "\n".join(body)

    async def get_subtree(self, node_hash: bytes) -> Coroutine[Any, Any, SubTree]:
        if node_hash == EmptyNode.hash:
            return SubTree([0], [EmptyNode()], self.hasher)

        data = await self._db.get(node_hash)
        self.stats["db_get"] += 1
        if not data:
            raise MissingNodeError

        structure, nodes = SubTree.parse(data, self.key_length)
        return SubTree(structure, nodes, self.hasher)

    async def set_subtree(self, subtree: SubTree) -> None:
        await self._db.set(subtree.hash, subtree.data)
        self.stats["db_set"] += 1

    async def write_to_db(self) -> None:
        # re batch in memory nodes and write subtrees to db
        await self._db.write()

    async def update(
        self,
        keys: list[bytes],
        values: list[bytes],
    ) -> Coroutine[Any, Any, SubTree]:
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """

        if len(keys) == 0:
            return self.root

        self.root = await self._update_subtree(keys, values, self.root, 0)
        await self.write_to_db()
        return self.root

    async def _update_subtree(
        self,
        keys: list[bytes],
        values: list[bytes],
        current_subtree: SubTree,
        height: int
    ) -> Coroutine[Any, Any, SubTree]:

        self.stats["update_subtree_calls"] += 1
        # assert len(keys) == len(values)
        assert (height%self.subtree_height) == 0
        if len(keys) == 0:
            return current_subtree

        bin_keys: list[list[bytes]] = [[] for _ in range(self.max_number_of_nodes)]
        bin_values: list[list[bytes]] = [[] for _ in range(self.max_number_of_nodes)]
        b = height // 8
        
        for i in range(len(keys)):
            k, v = keys[i], values[i]


            if self.subtree_height == 4:
                if height%8 == 0: #upper half
                    bin_idx = k[b] >> 4
                elif height%8 == 4: #lower half
                    bin_idx = k[b] & 15
                else:
                    raise InvalidKeyError
            elif self.subtree_height == 8:
                bin_idx = k[b]
            
            bin_keys[bin_idx].append(k)
            bin_values[bin_idx].append(v)
            

        layer_nodes = []
        layer_structure = []
        V = 0
        for i in range(len(current_subtree.nodes)):
            h = current_subtree.structure[i]
            current_node = current_subtree.nodes[i]
            incr = 1 << (self.subtree_height - h) 
            base_length = list(accumulate([len(b) for b in bin_keys[V: V + incr]]))

            _nodes, _heights = await self._update_node(
                bin_keys[V: V + incr], bin_values[V: V + incr], base_length, 0, current_node, height, h
            )
            layer_nodes += _nodes
            layer_structure += _heights
            V += incr

        assert V == self.max_number_of_nodes

        # new_subtree = SubTree(new_structure, new_nodes, self.hasher)

        # go through nodes again and push up empty nodes and single leaves, recursively
        for height in reversed(range(1, max(layer_structure) + 1)):
            next_layer_nodes: list[TreeNode] = []
            next_layer_structure: list[int] = []
            i = 0
            while i < len(layer_nodes):
                # pair node with next one
                if layer_structure[i] == height:
                    #Push up empty node
                    if isinstance(layer_nodes[i], EmptyNode) and isinstance(layer_nodes[i+1], EmptyNode):
                        parent_node = layer_nodes[i]
                    #Push up leaf node
                    elif isinstance(layer_nodes[i], EmptyNode) and isinstance(layer_nodes[i+1], LeafNode):
                        parent_node = layer_nodes[i+1]
                    #Push up leaf node
                    elif isinstance(layer_nodes[i], LeafNode) and isinstance(layer_nodes[i+1], EmptyNode):
                        parent_node = layer_nodes[i]
                    #Push up subtree node holding lower nodes. It will be unpacked later on
                    else:
                        if isinstance(layer_nodes[i], SubTree):
                            left_nodes = layer_nodes[i].nodes
                            left_structure = layer_nodes[i].structure
                        else:
                            left_nodes = [layer_nodes[i]]
                            left_structure = [layer_structure[i]]
                        if isinstance(layer_nodes[i+1], SubTree):
                            right_nodes = layer_nodes[i+1].nodes
                            right_structure = layer_nodes[i+1].structure
                        else:
                            right_nodes = [layer_nodes[i+1]]
                            right_structure = [layer_structure[i+1]]
                        parent_node = SubTree(left_structure + right_structure, left_nodes + right_nodes, self.hasher)

                    next_layer_nodes.append(parent_node)
                    next_layer_structure.append(layer_structure[i] - 1)
                    i += 1 
                # else just pass it up to next layer
                else:
                    next_layer_nodes.append(layer_nodes[i])
                    next_layer_structure.append(layer_structure[i])
                i += 1
            layer_nodes = list(next_layer_nodes)
            layer_structure = list(next_layer_structure)

        assert len(layer_nodes) == 1
        if isinstance(layer_nodes[0], SubTree):
            # the last node is already a subtree, just assign it
            new_subtree = layer_nodes[0]
        else:
            #the last node is an empty or leaf node, create a fake subtree that will be unpacked later
            new_subtree = SubTree([0], layer_nodes, self.hasher)

        await self.set_subtree(new_subtree)
        return new_subtree

    async def _update_node(
        self,
        keys: list[list[bytes]],
        values: list[list[bytes]],
        bin_length: list[int],
        base_length: int,
        current_node: TreeNode,
        height: int,
        h: int,
    ) -> Coroutine[Any, Any, tuple[list[TreeNode], list[int]]]:
        assert height + h< 8 * self.key_length
        assert len(keys) == len(values)
        self.stats["update_node_calls"] += 1

        # total_data = sum([len(k) for k in keys])
        total_data = bin_length[-1] - base_length
        if total_data == 0:
            return ([current_node], [h])
        
        if total_data == 1:
            idx = bin_length.index(base_length + 1)
            
            if isinstance(current_node, EmptyNode):
                # if the update value is non-empty, return a new leaf
                if len(values[idx][0]) != 0:
                    new_leaf = LeafNode(keys[idx][0], values[idx][0])
                    self.stats["leaf_created"] += 1
                    return ([new_leaf], [h])
                # else return the empty node (deleting an empty node)
                return ([current_node], [h])

            
            if isinstance(current_node, LeafNode):
                if current_node.key == keys[idx][0]:
                    # if the update value is non-empty, update the leaf
                    if len(values[idx][0]) != 0:
                        new_leaf = LeafNode(keys[idx][0], values[idx][0])
                        self.stats["leaf_created"] += 1
                        return ([new_leaf], [h])
                    # else return the empty node (deleting a leaf node)
                    return ([EmptyNode()], [h])
                
        
        #If we are at the bottom of the tree, we call update_subtree and return update nodes
        if h == self.subtree_height:
            
            if isinstance(current_node, StubNode):
                # StubNode  can only be stored at bottom of subtree
                btm_subtree = await self.get_subtree(current_node.hash)
                await self._db.delete(current_node.hash)
                self.stats["db_delete"] += 1
               
            elif isinstance(current_node, EmptyNode):
                btm_subtree = await self.get_subtree(EmptyNode.hash)

            elif isinstance(current_node, LeafNode):
                btm_subtree = SubTree([0], [current_node], self.hasher)
                
            else:
                raise InvalidDataError

            assert len(keys) == len(values) == 1
            new_subtree = await self._update_subtree(keys[0], values[0], btm_subtree, height + h)
            # return ([StubNode(new_subtree.hash)], [h])
            if len(new_subtree.nodes) == 1:
                # stub is empty or leaf
                return ([new_subtree.nodes[0]], [h])
            # return new stub from subtree
            return ([StubNode(new_subtree.hash)], [h])
        
        #Else, we just call _update_node and return the returned values
        if isinstance(current_node, EmptyNode):
            left_node = EmptyNode()
            right_node = EmptyNode()
        elif isinstance(current_node, LeafNode):
            if is_bit_set(current_node.key, height + h):
                left_node = EmptyNode()
                right_node = current_node
            else:
                left_node = current_node
                right_node = EmptyNode()
        else:
            print(type(current_node))
            raise InvalidDataError

        idx = len(keys)//2
        left_nodes, left_heights = await self._update_node(
            keys[:idx], values[:idx], bin_length[:idx], base_length, left_node, height, h + 1
        )
        right_nodes, right_heights = await self._update_node(
            keys[idx:], values[idx:], bin_length[idx:], bin_length[idx-1], right_node, height, h + 1
        )

        return (left_nodes + right_nodes, left_heights + right_heights)
