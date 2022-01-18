from .constants import DEFAULT_KEY_LENGTH, EMPTY_HASH, EMPTY_VALUE, LEAF_PREFIX
from .types import LeafNode, BranchNode, EmptyNode
from .utils import parse_branch_data, parse_leaf_data, binary_expansion
from typing import Coroutine, Any


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
        self.root_hash = EMPTY_HASH
        self._db = MockDB()
    
    async def get_node(self, node_hash: bytes) -> Coroutine[Any, Any, TreeNode]:
        if node_hash == EMPTY_HASH:
            return EmptyNode()
        
        data = await self._db.get(node_hash)

        if  not data:
            raise MissingNodeError

        if data.startswith(LEAF_PREFIX):
            key, value = parse_leaf_data(data, self.key_length)
            return LeafNode(key, value)

        left_hash, right_hash = parse_branch_data(data)

        return BranchNode(left_hash, right_hash)

    async def update(self, key: bytes, value: bytes) -> Coroutine[Any, Any, TreeNode]: 
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """
        if len(value) == 0:
            raise EmptyValueError

        if len(key) != self.key_length:
            raise InvalidKeyError

        root: TreeNode = await self.get_node(self.root_hash)
        current_node = root
        new_leaf = LeafNode(key, value)

        await self._db.set(new_leaf.hash, new_leaf.data)

        # if the current_node is EMPTY node then assign it to leaf node and return
        if isinstance(current_node, EmptyNode):
            root = new_leaf
            self.root_hash = root.hash

            return root

        binary_key: str = binary_expansion(key)

        h = 0
        ancestor_nodes: list[BranchNode] = []
        while isinstance(current_node, BranchNode):
            d = binary_key[h]
            # Append current_node to ancestor_nodes
            ancestor_nodes.append(current_node)
            if d == '0':
                current_node = await self.get_node(current_node.left_hash)
            elif d == '1':
                current_node = await self.get_node(current_node.right_hash)
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
            current_node_binary_key = binary_expansion(current_node.key)
            while binary_key[h] == current_node_binary_key[h]:
                # Create branch node with empty value
                new_branch = BranchNode(EMPTY_HASH, EMPTY_HASH)
                # Append defaultBranch to ancestor_nodes
                ancestor_nodes.append(new_branch)
                h += 1
            
            # Create last branch node, parent of node and new_leaf
            d = binary_key[h]
            if d == '0':
                bottom_node = BranchNode(new_leaf.hash, current_node.hash)
                await self._db.set(bottom_node.hash, bottom_node.data)
            elif d == '1':
                bottom_node = BranchNode(current_node.hash, new_leaf.hash)
                await self._db.set(bottom_node.hash, bottom_node.data)

        # Finally update all branch nodes in ancestor_nodes
        # Starting from the last
        while h > 0:
            p = ancestor_nodes[h - 1]
            await self._db.delete(p.hash)

            d = binary_key[h - 1]
            if d == '0':
                p.left_hash = bottom_node.hash
            elif d == '1':
                p.right_hash = bottom_node.hash
            
            await self._db.set(p.hash, p.data)
            bottom_node = p
            h -= 1
        
        self.root_hash = bottom_node.hash

        return bottom_node


    async def update_batch(self, data: list[tuple[bytes, bytes]]) -> Coroutine[Any, Any, TreeNode]: 
        """
        As specified in from https:#github.com/LiskHQ/lips/blob/master/proposals/lip-0039.md
        """

        if len(data) == 1:
            return self.update(*data[0])

        for key, value in data:
            if len(value) == 0:
                raise EmptyValueError

            if len(key) != self.key_length:
                raise InvalidKeyError
        
        root: TreeNode = await self.get_node(self.root_hash)
        current_node = root

        # if the current_node is EMPTY node then assign it to leaf node
        # and call update_batch recursively
        if isinstance(current_node, EmptyNode):
            key, value = data[0]
            root = LeafNode(key, value)
            self.root_hash = root.hash

            return self.update_batch(data[1:])
        
        new_root = await self._update_batch(data, current_node, 0)

    async def _update_batch(self, data: list[tuple[bytes, bytes]], head: TreeNode, h: int) -> Coroutine[Any, Any, TreeNode]: 


        
        ancestor_nodes: list[BranchNode] = []

        if isinstance(head, BranchNode):
            d = binary_key[h]
            # Append current_node to ancestor_nodes
            ancestor_nodes.append(head)
            if d == '0':
                current_node = await self.get_node(head.left_hash)
                data = [(k, v) for k, v in data if binary_expansion(k)[h] == "0"]
                left_hash = await self._update_batch(data, current_node, h + 1)
            elif d == '1':
                current_node = await self.get_node(head.right_hash)
                data = [(k, v) for k, v in data if binary_expansion(k)[h] == "1"]
                right_hash = await self._update_batch(data, current_node, h + 1)



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
            current_node_binary_key = binary_expansion(current_node.key)
            while binary_key[h] == current_node_binary_key[h]:
                # Create branch node with empty value
                new_branch = BranchNode(EMPTY_HASH, EMPTY_HASH)
                # Append defaultBranch to ancestor_nodes
                ancestor_nodes.append(new_branch)
                h += 1
            
            # Create last branch node, parent of node and new_leaf
            d = binary_key[h]
            if d == '0':
                bottom_node = BranchNode(new_leaf.hash, current_node.hash)
                await self._db.set(bottom_node.hash, bottom_node.data)
            elif d == '1':
                bottom_node = BranchNode(current_node.hash, new_leaf.hash)
                await self._db.set(bottom_node.hash, bottom_node.data)

        # Finally update all branch nodes in ancestor_nodes
        # Starting from the last
        print(len(ancestor_nodes), h)
        while h > 0:
            p = ancestor_nodes[h - 1]
            d = binary_key[h - 1]
            if d == '0':
                p.left_hash = bottom_node.hash
            elif d == '1':
                p.right_hash = bottom_node.hash
            
            await self._db.set(p.hash, p.data)
            bottom_node = p
            h -= 1
        
        self.root_hash = bottom_node.hash

        return bottom_node  

#     public async remove(key: Buffer): Promise<TreeNode> {
#         if (key.length !== self.key_length) {
#             throw new Error(`Key is not equal to defined key length of ${self.key_length}`)
#         }

#         ancestor_nodes: TreeNode[] = []
#         binary_key = binary_expansion(key, self.key_length)
#         current_node = await self.get_node(self._root_hash)
#         h = 0
#         current_nodeSibling: TreeNode = new Empty()

#         # Collect all ancestor nodes through traversing the binary expansion by height
#         # End of the loop ancestor_nodes has all the branch nodes
#         # current_node will be the leaf/node we are looking to remove
#         while (current_node instanceof Branch) {
#             ancestor_nodes.append(current_node)
#             d = binary_key[h]
#             if (d === '0') {
#                 current_nodeSibling = await self.get_node(current_node.right_hash)
#                 current_node = await self.get_node(current_node.left_hash)
#             elif (d === '1') {
#                 current_nodeSibling = await self.get_node(current_node.left_hash)
#                 current_node = await self.get_node(current_node.right_hash)
#             }
#             h += 1
#         }

#         # When current_node is empty, nothing to remove
#         if (current_node instanceof Empty) {
#             return current_node
#         }
#         # When the input key does not match node key, nothing to remove
#         if (!current_node.key.equals(key)) {
#             return current_node
#         }
#         bottom_node: TreeNode = new Empty()

#         # current_node has a branch sibling, delete current_node
#         if (current_nodeSibling instanceof Branch) {
#             await self._db.del(current_node.hash)
#         elif (current_nodeSibling instanceof Leaf) {
#             # current_node has a leaf sibling,
#             # remove the leaf and move sibling up the tree
#             await self._db.del(current_node.hash)
#             bottom_node = current_nodeSibling

#             h -= 1
#             # In order to move sibling up the tree
#             # an exact emptyHash check is required
#             # not using EMPTY_HASH here to make sure we use correct hash from Empty class
#             emptyHash = new Empty().hash
#             while (h > 0) {
#                 p = ancestor_nodes[h - 1] as Branch

#                 # if one of the children is empty then break the condition
#                 if (
#                     p instanceof Branch &&
#                     !p.left_hash.equals(emptyHash) &&
#                     !p.right_hash.equals(emptyHash)
#                 ) {
#                     break
#                 }

#                 await self._db.del(p.hash)
#                 h -= 1
#             }
#         }

#         # finally update all branch nodes in ancestor_nodes.
#         # note that h now is set to the correct height from which
#         # nodes have to be updated
#         while (h > 0) {
#             p = ancestor_nodes[h - 1]
#             d = binary_key.charAt(h - 1)

#             if (d === '0') {
#                 (p as Branch).update(bottom_node.hash, NodeSide.LEFT)
#             elif (d === '1') {
#                 (p as Branch).update(bottom_node.hash, NodeSide.RIGHT)
#             }
#             await self._db.set(p.hash, (p as Branch).data)
#             bottom_node = p
#             h -= 1
#         }
#         self._root_hash = bottom_node.hash

#         return bottom_node
#     }

#     public async generateSingleProof(queryKey: Buffer): Promise<SingleProof> {
#         rootNode = await self.get_node(self._root_hash)
#         current_node = rootNode
#         if (current_node instanceof Empty) {
#             return {
#                 key: queryKey,
#                 value: EMPTY_VALUE,
#                 binaryBitmap: bufferToBinaryString(EMPTY_VALUE),
#                 siblingHashes: [],
#                 ancestorHashes: [],
#             }
#         }

#         h = 0
#         siblingHashes = []
#         ancestorHashes = []
#         binaryBitmap = ''
#         binary_key = binary_expansion(queryKey, self.key_length)

#         while (current_node instanceof Branch) {
#             ancestorHashes.append(current_node.hash)
#             d = binary_key[h]
#             current_nodeSibling: TreeNode = new Empty()
#             if (d === '0') {
#                 current_nodeSibling = await self.get_node(current_node.right_hash)
#                 current_node = await self.get_node(current_node.left_hash)
#             elif (d === '1') {
#                 current_nodeSibling = await self.get_node(current_node.left_hash)
#                 current_node = await self.get_node(current_node.right_hash)
#             }

#             if (current_nodeSibling instanceof Empty) {
#                 binaryBitmap = `0${binaryBitmap}`
#             else
#                 binaryBitmap = `1${binaryBitmap}`
#                 siblingHashes.append(current_nodeSibling.hash)
#             }
#             h += 1
#         }

#         if (current_node instanceof Empty) {
#             # exclusion proof
#             return {
#                 siblingHashes,
#                 ancestorHashes,
#                 binaryBitmap,
#                 key: queryKey,
#                 value: EMPTY_VALUE,
#             }
#         }

#         if (!current_node.key.equals(queryKey)) {
#             # exclusion proof
#             ancestorHashes.append(current_node.hash) # in case the leaf is sibling to another node
#             return {
#                 siblingHashes,
#                 ancestorHashes,
#                 binaryBitmap,
#                 key: current_node.key,
#                 value: current_node.value,
#             }
#         }

#         # inclusion proof
#         ancestorHashes.append(current_node.hash) # in case the leaf is sibling to another node
#         return {
#             siblingHashes,
#             ancestorHashes,
#             binaryBitmap,
#             key: current_node.key,
#             value: current_node.value,
#         }
#     }

#     public async generateMultiProof(queryKeys: Buffer[]): Promise<Proof> {
#         partialQueries: SingleProof[] = []
#         for (queryKey of queryKeys) {
#             query = await self.generateSingleProof(queryKey)
#             partialQueries.append(query)
#         }

#         queries: Query[] = [...partialQueries].map(sp => ({
#             bitmap: binaryStringToBuffer(sp.binaryBitmap),
#             key: sp.key,
#             value: sp.value,
#         }))
#         siblingHashes: Buffer[] = []
#         ancestorHashes = [...partialQueries].map(sp => sp.ancestorHashes).flat()
#         sortedQueries: QueryWithHeight[] = [...partialQueries].map(sp => ({
#             binaryBitmap: sp.binaryBitmap,
#             key: sp.key,
#             value: sp.value,
#             siblingHashes: sp.siblingHashes,
#             height: sp.binaryBitmap.length,
#         }))
#         sortedQueries = sortByBitmapAndKey(sortedQueries)

#         while (sortedQueries.length > 0) {
#             sp = sortedQueries.shift()!
#             if (sp.height === 0) {
#                 continue
#             }
#             b = sp.binaryBitmap.charAt(sp.binaryBitmap.length - sp.height)
#             if (b === '1') {
#                 node_hash = sp.siblingHashes.pop()!
#                 isPresentInSiblingHashes = false
#                 isPresentInAncestorHashes = false
#                 for (i of siblingHashes) {
#                     if (i.equals(node_hash)) {
#                         isPresentInSiblingHashes = true
#                         break
#                     }
#                 }
#                 for (i of ancestorHashes) {
#                     if (i.equals(node_hash)) {
#                         isPresentInAncestorHashes = true
#                         break
#                     }
#                 }
#                 if (!isPresentInSiblingHashes && !isPresentInAncestorHashes) {
#                     # TODO : optimize this
#                     siblingHashes.append(node_hash)
#                 }
#             }
#             sp.height -= 1

#             if (sortedQueries.length > 0) {
#                 sortedQueriesWithbinary_key = sortedQueries.map(query => ({
#                     binary_key: binary_expansion(query.key, self.key_length),
#                     binaryBitmap: query.binaryBitmap,
#                     value: query.value,
#                     siblingHashes: query.siblingHashes,
#                     height: query.height,
#                 }))
#                 spWithbinary_key = {
#                     binary_key: binary_expansion(sp.key, self.key_length),
#                     binaryBitmap: sp.binaryBitmap,
#                     value: sp.value,
#                     siblingHashes: sp.siblingHashes,
#                     height: sp.height,
#                 }
#                 insertIndex = binarySearch(
#                     sortedQueriesWithbinary_key,
#                     callback => treeSort(spWithbinary_key, callback) < 0,
#                 )
#                 if (insertIndex === sortedQueries.length) {
#                     sortedQueries.append(sp)
#                 else
#                     keyPrefix = binary_expansion(sp.key, self.key_length).substring(0, sp.height)
#                     query = sortedQueries[insertIndex]

#                     if (!binary_expansion(query.key, self.key_length).endsWith(keyPrefix, query.height)) {
#                         sortedQueries.splice(insertIndex, 0, sp)
#                     }
#                 }
#             else
#                 sortedQueries.append(sp)
#             }
#         }

#         return { siblingHashes, queries }
#     }
# }
