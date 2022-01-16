from dataclasses import dataclass
from dingus.utils import hash
from .constants import LEAF_PREFIX, BRANCH_PREFIX, EMPTY_HASH

@dataclass
class LeafNode(object):
    key: bytes
    value: bytes

    @property
    def data(self) -> bytes:
        return LEAF_PREFIX + self.key + self.value
    @property
    def hash(self) -> bytes:
        return hash(self.data)

@dataclass
class BranchNode(object):
    left: bytes
    right: bytes

    @property
    def data(self) -> bytes:
        return BRANCH_PREFIX + self.left + self.right
    @property
    def hash(self) -> bytes:
        return hash(self.data)

@dataclass
class EmptyNode(object):

    @property
    def hash(self) -> bytes:
        return EMPTY_HASH
