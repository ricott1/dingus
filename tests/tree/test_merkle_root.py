from dingus.tree.utils import merkle_root
from dingus.tree.constants import EMPTY_HASH
import json


def test_empty_tree():
    assert merkle_root([]) == EMPTY_HASH


def test_fixtures():
    with open("tests/tree/fixtures/rmt.json", "r") as f:
        test_cases = json.load(f)["testCases"]

    for case in test_cases:
        _input = [bytes.fromhex(i) for i in case["input"]["values"]]
        _output = bytes.fromhex(case["output"]["merkleRoot"])
        assert merkle_root(_input) == _output
