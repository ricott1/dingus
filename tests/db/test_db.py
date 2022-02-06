import rocksdb


def test_put():
    db = rocksdb.DB("tests/db/test.db", rocksdb.Options(create_if_missing=True))
    db.put(b"a", b"b")
    print(db.get(b"a"))
