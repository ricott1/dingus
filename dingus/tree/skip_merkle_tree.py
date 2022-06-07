from itertools import accumulate
from typing import Coroutine, Any
import os.path

from .hasher import TreeHasher, ECCHasher
from .constants import (
    DEFAULT_KEY_LENGTH,
    DEFAULT_SUBTREE_MAX_HEIGHT,
    DEFAULT_HASHER,
    EMPTY_HASH,
    EMPTY_VALUE,
)
from .types import (
    BranchNode,
    LeafNode,
    Proof,
    Query,
    QueryWithProof,
    SubTree,
    EmptyNode,
    TreeNode,
    StubNode,
)
from .errors import *
from .utils import binary_expansion, binary_search, is_bit_set, binary_to_bytes
from dingus.db import InMemoryDB, RocksDB


class SkipMerkleTree(object):
    def __init__(
        self,
        key_length: int = DEFAULT_KEY_LENGTH,
        subtree_height: int = DEFAULT_SUBTREE_MAX_HEIGHT,
        db: str = "inmemorydb",
        hasher=DEFAULT_HASHER,
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

    async def print(self, subtree: SubTree, preamble: str = " ", hash_length: int = 4) -> str:
        BROWN = lambda t: f"\u001b[38;2;{105};{103};{60}m" + t + "\u001b[0m"
        head = f"{preamble*self.subtree_height}R:{subtree.hash.hex()[:hash_length]}\n"
        body = []
        for i in reversed(range(len(subtree.nodes))):
            h, node = subtree.structure[i], subtree.nodes[i]
            if i > 0:
                connector = "├"
            else:
                connector = "╰"
            if isinstance(node, EmptyNode):
                body.append(preamble * self.subtree_height + connector + "──" * h + f"─<∅{h}")

            elif isinstance(node, LeafNode):
                key = node.key[:4]
                bin_key = bin(int.from_bytes(key, "big")).lstrip("0b").zfill(8 * len(key))

                body.append(
                    preamble * self.subtree_height
                    + connector
                    + "──" * h
                    + f"─<🌿{h} {node.key.hex()[:hash_length]}->{node.hash.hex()[:hash_length]}"
                    # + f"─<🌿{h}:{bin_key[:0]}->{node.key.hex()[:hash_length]}:{node.hash.hex()[:hash_length]}"
                )
            elif isinstance(node, StubNode):
                current_subtree = await self.get_subtree(node.hash)
                ctp = await self.print(current_subtree, preamble + "  ")
                _body = "\n".join(
                    [
                        f"{BROWN('─<B')}:{node.hash.hex()[:hash_length]}",
                        f"{preamble*self.subtree_height}{BROWN('├')}{ctp}",
                    ]
                )

                body.append(preamble * self.subtree_height + connector + "──" * h + _body)
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
        height: int,
        is_deleting: bool = True,
    ) -> Coroutine[Any, Any, SubTree]:

        self.stats["update_subtree_calls"] += 1
        assert len(keys) == len(values)
        assert (height % self.subtree_height) == 0
        if len(keys) == 0:
            return current_subtree

        bin_keys: list[list[bytes]] = [[] for _ in range(self.max_number_of_nodes)]
        bin_values: list[list[bytes]] = [[] for _ in range(self.max_number_of_nodes)]
        b = height // 8

        for i in range(len(keys)):
            k, v = keys[i], values[i]

            if self.subtree_height == 4:
                if height % 8 == 0:  # upper half
                    bin_idx = k[b] >> 4
                elif height % 8 == 4:  # lower half
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
            base_length = list(accumulate([len(b) for b in bin_keys[V : V + incr]]))

            _nodes, _heights = await self._update_node(
                bin_keys[V : V + incr],
                bin_values[V : V + incr],
                base_length,
                0,
                current_node,
                height,
                h,
            )
            layer_nodes += _nodes
            layer_structure += _heights
            V += incr

        assert V == self.max_number_of_nodes

        if is_deleting:
            # go through nodes again and push up empty nodes and single leaves, recursively
            # this step is actually necessary only if we deleted some keys
            for height in reversed(range(1, max(layer_structure) + 1)):
                next_layer_nodes: list[TreeNode] = []
                next_layer_structure: list[int] = []
                i = 0
                while i < len(layer_nodes):
                    # pair node with next one
                    if layer_structure[i] == height:
                        # Push up empty node
                        if isinstance(layer_nodes[i], EmptyNode) and isinstance(layer_nodes[i + 1], EmptyNode):
                            parent_node = layer_nodes[i]
                        # Push up leaf node
                        elif isinstance(layer_nodes[i], EmptyNode) and isinstance(layer_nodes[i + 1], LeafNode):
                            parent_node = layer_nodes[i + 1]
                        # Push up leaf node
                        elif isinstance(layer_nodes[i], LeafNode) and isinstance(layer_nodes[i + 1], EmptyNode):
                            parent_node = layer_nodes[i]
                        # Push up subtree node holding lower nodes. It will be unpacked later on
                        else:
                            if isinstance(layer_nodes[i], SubTree):
                                left_nodes = layer_nodes[i].nodes
                                left_structure = layer_nodes[i].structure
                            else:
                                left_nodes = [layer_nodes[i]]
                                left_structure = [layer_structure[i]]
                            if isinstance(layer_nodes[i + 1], SubTree):
                                right_nodes = layer_nodes[i + 1].nodes
                                right_structure = layer_nodes[i + 1].structure
                            else:
                                right_nodes = [layer_nodes[i + 1]]
                                right_structure = [layer_structure[i + 1]]
                            parent_node = SubTree(
                                left_structure + right_structure,
                                left_nodes + right_nodes,
                                self.hasher,
                            )

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
                # the last node is an empty or leaf node, create a fake subtree that will be unpacked later
                new_subtree = SubTree([0], layer_nodes, self.hasher)

        else:
            # we do not need to push up anything
            new_subtree = SubTree(layer_structure, layer_nodes, self.hasher)

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
        assert height + h < 8 * self.key_length
        assert len(keys) == len(values)
        self.stats["update_node_calls"] += 1

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

        # If we are at the bottom of the tree, we call update_subtree and return update nodes
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
            if len(new_subtree.nodes) == 1:
                # stub is empty or leaf
                return ([new_subtree.nodes[0]], [h])
            return ([StubNode(new_subtree.hash)], [h])

        # Else, we just call _update_node and return the returned values
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

        idx = len(keys) // 2
        left_nodes, left_heights = await self._update_node(
            keys[:idx],
            values[:idx],
            bin_length[:idx],
            base_length,
            left_node,
            height,
            h + 1,
        )
        right_nodes, right_heights = await self._update_node(
            keys[idx:],
            values[idx:],
            bin_length[idx:],
            bin_length[idx - 1],
            right_node,
            height,
            h + 1,
        )

        return (left_nodes + right_nodes, left_heights + right_heights)

    async def generate_proof(self, query_keys: list[bytes]) -> Proof:
        if len(query_keys) == 0:
            return Proof([], [])

        query_proofs: list[QueryWithProof] = [await self._generate_query_proof(self.root, k, 0) for k in query_keys]
        # prepare queries from single proofs, maintaining original order (same as query keys)
        queries: list[Query] = [Query(sp.key, sp.value, sp.bitmap) for sp in query_proofs]
        # sort by largest height (bottom first), smaller key (left first)
        query_proofs = sorted(query_proofs, key=lambda q: (-q.height, q.key))
        sibling_hashes: list[bytes] = []
        ancestor_hashes: list[bytes] = [h for sp in query_proofs for h in sp.ancestor_hashes]

        while len(query_proofs) > 0:
            sp = query_proofs.pop(0)
            if sp.height == 0:
                continue

            if sp.binary_bitmap[0] == "1":
                node_hash = sp.sibling_hashes.pop()
                if not node_hash in sibling_hashes and not node_hash in ancestor_hashes:
                    sibling_hashes.append(node_hash)

            sp.binary_bitmap = sp.binary_bitmap[1:]
            query_proofs = insert_and_filter_queries(sp, query_proofs)

        return Proof(sibling_hashes, queries)

    async def _generate_query_proof(self, current_subtree: SubTree, query_key: bytes, height: int) -> QueryWithProof:
        if len(query_key) != self.key_length:
            raise Exception('Invalid length of query_key')
        b = height // 8
        if self.subtree_height == 4:
            if height % 8 == 0:  # upper half
                bin_idx = query_key[b] >> 4
            elif height % 8 == 4:  # lower half
                bin_idx = query_key[b] & 15
            else:
                raise InvalidKeyError
        elif self.subtree_height == 8:
            bin_idx = query_key[b]
        print("\nCURRENT SUBTREE, ", height, current_subtree.structure)
        V = 0
        for i in range(len(current_subtree.nodes)):
            h = current_subtree.structure[i]
            current_node = current_subtree.nodes[i]
            incr = 1 << (self.subtree_height - h)
            if V <= bin_idx < V + incr:
                break 
            V += incr

        
        
        ancestor_hashes = []
        sibling_hashes = []

        nodes = list(current_subtree.nodes)
        structure = list(current_subtree.structure)
        binary_bitmap = ""
        
        query_height = int(h)
        target_node = current_node

        # Calculate ancestor and sibling hashes using the target_node as starting point
        # Recalculate internal hashes from the stored current_subtree.nodes, while apending to sibling_hashes the one needed in the queried path.
        for s in reversed(range(1, max(structure) + 1)):
            _nodes = []
            _structure = []

            i = 0
            while i < len(nodes):
                if structure[i] == s:
                    parent_node = BranchNode(nodes[i].hash, nodes[i + 1].hash)
                    _nodes.append(parent_node)
                    _structure.append(structure[i] - 1)
                    # check if the target node is the next
                    # 'is' operator checks equality of pointers
                    if target_node is nodes[i]:
                        ancestor_hashes.insert(0, parent_node.hash)
                        target_node = parent_node
                        if isinstance(nodes[i + 1], EmptyNode):
                            binary_bitmap = binary_bitmap + "0"
                        else:
                            binary_bitmap = binary_bitmap + "1"
                            sibling_hashes.insert(0, nodes[i + 1].hash)
                    # 'is' operator checks equality of pointers
                    elif target_node is nodes[i + 1]:
                        ancestor_hashes.insert(0, parent_node.hash)
                        target_node = parent_node
                        if isinstance(nodes[i], EmptyNode):
                            binary_bitmap = binary_bitmap + "0"
                        else:
                            binary_bitmap = binary_bitmap + "1"
                            sibling_hashes.insert(0, nodes[i].hash)
                    i += 1
                else:
                    _nodes.append(nodes[i])
                    _structure.append(structure[i])
                i += 1
            nodes = _nodes
            structure = _structure

        if isinstance(current_node, EmptyNode):
            return QueryWithProof(query_key, EMPTY_VALUE, binary_to_bytes(binary_bitmap), ancestor_hashes, sibling_hashes)

        elif isinstance(current_node, LeafNode):
            ancestor_hashes.append(current_node.hash)
            return QueryWithProof(
                current_node.key,
                current_node.value,
                binary_to_bytes(binary_bitmap),
                ancestor_hashes,
                sibling_hashes,
            )

        elif isinstance(current_node, StubNode):
            assert height % self.subtree_height == 0
            lower_subtree = await self.get_subtree(current_node.hash)
            lower_query_proof: QueryWithProof = await self._generate_query_proof(lower_subtree, query_key, height + query_height)
            # In the skip Merkle tree we have to handle hashes and bitmap from lower layers
           
            return QueryWithProof(
                lower_query_proof.key,
                lower_query_proof.value,
                binary_to_bytes(lower_query_proof.binary_bitmap + binary_bitmap),
                ancestor_hashes + lower_query_proof.ancestor_hashes,
                sibling_hashes + lower_query_proof.sibling_hashes,
            )


def insert_and_filter_queries(q: QueryWithProof or Query, queries: list[QueryWithProof or Query]) -> list[QueryWithProof or Query]:
    if len(queries) > 0:
        insert_index = binary_search(
            queries,
            lambda p: (q.height == p.height and q.key < p.key) or (q.height > p.height),
        )

        if insert_index == len(queries):
            queries.append(q)
        else:
            p = queries[insert_index]
            if not p.binary_path.endswith(q.binary_path, p.height):
                queries.insert(insert_index, q)
    else:
        queries.append(q)

    return queries


def verify(query_keys: list[bytes], proof: Proof, merkle_root: bytes, key_length: int = DEFAULT_KEY_LENGTH) -> bool:
    if len(query_keys) != len(proof.queries):
        return False

    for key, query in zip(query_keys, proof.queries):
        # q is an inclusion proof for k or a default empty node
        if len(key) != key_length:
            return False
        if key == query.key:
            continue

        # q is an inclusion proof for another leaf node
        common_prefix = os.path.commonprefix([binary_expansion(query.key), binary_expansion(key)])
        if len(query.binary_bitmap) > len(common_prefix):
            # q does not give an non-inclusion proof for k
            return False

    
    filtered_queries = []
    filter: dict[bytes, bool] = {}
    for q in proof.queries:
        # Remove duplicate queries preserving order. This can happen if the same query is given for different query_keys, as for inclusion proofs or non-inclusion proofs pointing to a leaf node
        if q.binary_path not in filter:
            filtered_queries.append(q)
            filter[q.binary_path] = True
        # Remove non-inclusion proofs pointing to the same empty node. This is more tricky since the query could be different (different queired keys which are not overwritten in the query)
        # To do this, we check only empty
    return calculate_root(proof.sibling_hashes, filtered_queries) == merkle_root


def calculate_root(sibling_hashes: list[bytes], queries: list[Query]) -> bytes:
    sorted_queries = sorted(queries, key=lambda q: (-q.height, q.key))

    while len(sorted_queries) > 0:
        q = sorted_queries.pop(0)

        # We reached the top of the tree, return merkle root
        if q.height == 0:
            # To avoid appending useless bits to all query bitmaps
            assert len(q.binary_bitmap) == 0
            return q.hash

        # we distinguish three cases for the sibling hash:
        # 1. sibling is next element of sorted_queries
        if len(sorted_queries) > 0 and q.is_sibling_of(sorted_queries[0]):
            sibling_hash = sorted_queries[0].hash
            del sorted_queries[0]
        # 2. sibling is default empty node
        elif q.binary_bitmap[0] == "0":
            sibling_hash = EMPTY_HASH
        # 3. sibling hash comes from sibling_hashes
        elif q.binary_bitmap[0] == "1":
            sibling_hash = sibling_hashes.pop(0)

        d = q.binary_key[q.height - 1]
        if d == "0":
            print(f"Hashing at h={len(q.binary_bitmap)}", q.hash.hex()[:4], sibling_hash.hex()[:4], " --> ", BranchNode(q.hash, sibling_hash).hash.hex()[:4])
            q.hash = BranchNode(q.hash, sibling_hash).hash
        elif d == "1":
            print(f"Hashing at h={len(q.binary_bitmap)}", sibling_hash.hex()[:4], q.hash.hex()[:4], " --> ", BranchNode(sibling_hash, q.hash).hash.hex()[:4])
            q.hash = BranchNode(sibling_hash, q.hash).hash

        q.binary_bitmap = q.binary_bitmap[1:]
        sorted_queries = insert_and_filter_queries(q, sorted_queries)

    raise Exception("Can not calculate root hash")


def is_inclusion_proof(query_key: bytes, query: Query) -> bool:
    return query_key == query.key and query.value != EMPTY_VALUE
