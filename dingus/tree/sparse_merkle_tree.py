from .constants import DEFAULT_KEY_LENGTH, EMPTY_HASH, LEAF_PREFIX
from .types import LeafNode, BranchNode, EmptyNode
from .utils import split_keys, is_bit_set
from typing import Coroutine, Any
import asyncio


TreeNode = LeafNode | BranchNode | EmptyNode

class MissingNodeError(Exception):
    pass

class EmptyValueError(Exception):
    pass

class InvalidKeyError(Exception):
    pass


class MockDB(object):
    def __init__(self) -> None:
        self.kv = {}
    
    async def set(self, key: bytes, value: bytes) -> None:
        self.kv[key] = value
    
    async def get(self, key: bytes) -> bytes:
        if key in self.kv:
            return self.kv[key]
        return b""
    
    async def delete(self, key: bytes) -> None:
        if key in self.kv:
            del self.kv[key]

class SparseMerkleTree(object):
    def __init__(self, key_length: int = DEFAULT_KEY_LENGTH) -> None:
        self.key_length = key_length
        self.root = EmptyNode()
        self._db = MockDB()

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

    async def get_node(self, node_hash: bytes) -> Coroutine[Any, Any, TreeNode]:
        if node_hash == EmptyNode().hash:
            return EmptyNode()
        
        data = await self._db.get(node_hash)

        if not data:
            raise MissingNodeError

        if data.startswith(LEAF_PREFIX):
            key, value = LeafNode.parse(data, self.key_length)
            return LeafNode(key, value)

        left_hash, right_hash = BranchNode.parse(data)
        return BranchNode(left_hash, right_hash)

    async def update(self, key: bytes, value: bytes) -> Coroutine[Any, Any, TreeNode]: 
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """

        if len(value) == 0:
            raise EmptyValueError

        if len(key) != self.key_length:
            raise InvalidKeyError

        self.root = await self._update(key, value, self.root, 0)
        return self.root
    
    async def _update(self, key: bytes, value: bytes, current_node: TreeNode, height: int = 0) -> Coroutine[Any, Any, TreeNode]:
        
        new_leaf = LeafNode(key, value)
        await self._db.set(new_leaf.hash, new_leaf.data)

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
                new_branch = BranchNode(EMPTY_HASH, EMPTY_HASH)
                # Append defaultBranch to ancestor_nodes
                ancestor_nodes.append(new_branch)
                h += 1 
            # Create last branch node, parent of node and new_leaf

            if is_bit_set(key, h):
                bottom_node = BranchNode(current_node.hash, new_leaf.hash)
            else:
                bottom_node = BranchNode(new_leaf.hash, current_node.hash)
            await self._db.set(bottom_node.hash, bottom_node.data)

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
            
            await self._db.set(p.hash, p.data)
            bottom_node = p

        return bottom_node
    
    

    async def update_batch(self, data: list[tuple[bytes, bytes]], strict: bool = False) -> Coroutine[Any, Any, TreeNode]: 
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
        self.root = await self._update_batch(sorted_data, self.root, 0)
        return self.root
        
    async def _update_batch(self, data: list[tuple[bytes, bytes]], current_node: TreeNode, height: int) -> Coroutine[Any, Any, TreeNode]: 
        assert height < 8 * self.key_length
        if len(data) == 0:
            return current_node
        if len(data) == 1:
            key, value = data[0]
            return await self._update(key, value, current_node, height)

        # If current_node is a leaf, append it to data
        if isinstance(current_node, LeafNode):
            data.append((current_node.key, current_node.value))
            data = sorted(data, key=lambda d: d[0])

        keys = [d[0] for d in data]
        idx = split_keys(keys, lambda k: is_bit_set(k, height))
        left_data = data[:idx]
        right_data = data[idx:]
        concurrent_update = height < 2 and left_data and right_data

        if isinstance(current_node, LeafNode) or isinstance(current_node, EmptyNode):
            left_node = EmptyNode()
            right_node = EmptyNode()
        elif isinstance(current_node, BranchNode): 
            left_node = await self.get_node(current_node.left_hash)
            right_node = await self.get_node(current_node.right_hash)

        if concurrent_update:
            left_node, right_node = await asyncio.gather(
                self._update_batch(left_data, left_node, height + 1),
                self._update_batch(right_data, right_node, height + 1)
            )
        else:
            if left_data:
                left_node = await self._update_batch(left_data, left_node, height + 1)
            if right_data:
                right_node = await self._update_batch(right_data, right_node, height + 1)

        await self._db.delete(current_node.hash)
        current_node = BranchNode(left_node.hash, right_node.hash)
        await self._db.set(current_node.hash, current_node.data)
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
                if p.left_hash != EmptyNode().hash and p.right_hash!= EmptyNode().hash:
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

            await self._db.set(p.hash, p.data)
            bottom_node = p
            
        self.root = bottom_node
        return bottom_node
