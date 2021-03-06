from dingus.utils import hash

LEAF_PREFIX = b"\x00"
BRANCH_PREFIX = b"\x01"
INTERNAL_LEAF_PREFIX = b"\x02"
EMPTY_HASH_PLACEHOLDER_PREFIX = b"\x02"

DEFAULT_KEY_LENGTH = 32
DEFAULT_SUBTREE_MAX_HEIGHT = 8
DEFAULT_SUBTREE_NODES = 1 << DEFAULT_SUBTREE_MAX_HEIGHT

DEFAULT_HASHER = "tree"

EMPTY_VALUE = b""
EMPTY_HASH = hash(EMPTY_VALUE)

NODE_HASH_SIZE = len(EMPTY_HASH)
