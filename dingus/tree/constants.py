from dingus.crypto import hash

LEAF_PREFIX = bytes.fromhex("00")
BRANCH_PREFIX = bytes.fromhex("01")
INTERNAL_LEAF_PREFIX = bytes.fromhex("02")
EMPTY_HASH_PLACEHOLDER_PREFIX = bytes.fromhex("02")

DEFAULT_KEY_LENGTH = 32
DEFAULT_SUBTREE_MAX_HEIGHT = 8
DEFAULT_SUBTREE_NODES = 1 << DEFAULT_SUBTREE_MAX_HEIGHT

DEFAULT_HASHER = "tree"

EMPTY_VALUE = b""
EMPTY_HASH = hash(EMPTY_VALUE)

NODE_HASH_SIZE = len(EMPTY_HASH)
