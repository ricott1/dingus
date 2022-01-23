from dataclasses import dataclass
from dingus.utils import hash
from .constants import DEFAULT_KEY_LENGTH, LEAF_PREFIX, BRANCH_PREFIX, EMPTY_HASH, NODE_HASH_SIZE

@dataclass
class LeafNode(object):
    key: bytes
    value: bytes

    @classmethod
    def parse(cls, data: bytes, key_length: int = DEFAULT_KEY_LENGTH) -> tuple[bytes, bytes]:
        key = data[len(LEAF_PREFIX):key_length + len(LEAF_PREFIX)]
        value = data[key_length + len(LEAF_PREFIX):]
        return (key, value)

    @property
    def data(self) -> bytes:
        return LEAF_PREFIX + self.key + self.value
    @property
    def hash(self) -> bytes:
        return hash(self.data)

@dataclass
class BranchNode(object):
    left_hash: bytes
    right_hash: bytes

    @classmethod
    def parse(cls, data: bytes) -> tuple[bytes, bytes]:
        left_hash = data[-2 * NODE_HASH_SIZE: -1 * NODE_HASH_SIZE]
        right_hash = data[-1 * NODE_HASH_SIZE:]
        return (left_hash, right_hash)

    @property
    def data(self) -> bytes:
        return BRANCH_PREFIX + self.left_hash + self.right_hash
    @property
    def hash(self) -> bytes:
        return hash(self.data)

@dataclass
class EmptyNode(object):

    @property
    def hash(self) -> bytes:
        return EMPTY_HASH
