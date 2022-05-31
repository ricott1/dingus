import os
from dingus.utils import hash

KEY_LENGTH = 32


def create_fixed():
    return [
        (
            bytes.fromhex(
                "1031ea63d17304808ab76de5ccbad10e26441a3207f5947455eb99f040ea1800"
            ),
            hash(bytes.fromhex("00")),
        ),
        (
            bytes.fromhex(
                "a131ea63d17304808ab76de5ccbad10e26441a3207f5947455eb99f040ea1800"
            ),
            hash(bytes.fromhex("01")),
        ),
        (
            bytes.fromhex(
                "1231ea63d17304808ab76de5ccbad10e26441a3207f5947455eb99f040ea1800"
            ),
            hash(bytes.fromhex("02")),
        ),
        (
            bytes.fromhex(
                "2032ea63d17304808ab76de5ccbad10e26441a3207f5947455eb99f040ea1800"
            ),
            hash(bytes.fromhex("05")),
        ),
        (
            bytes.fromhex(
                "1036ea63d17304808ab76de5ccbad10e26441a3207f5947455eb99f040ea1800"
            ),
            hash(bytes.fromhex("06")),
        ),
    ]


def create_test_case(n: int, key_length: int = KEY_LENGTH) -> list[tuple[bytes, bytes]]:
    keys = sorted([os.urandom(key_length) for _ in range(n)])
    keys_set = {}
    for i, key in enumerate(keys):
        if key in keys_set:
            keys.pop(i)
        keys_set[key] = True

    values = [hash(k) for k in keys]

    return (keys, values)
