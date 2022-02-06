# import rocksdb
# import os
# from pathlib import Path


class RocksDB(object):
    def __init__(self, filename: str = "") -> None:
        return
        opts = rocksdb.Options()
        opts.create_if_missing = True
        opts.max_open_files = 300000
        opts.write_buffer_size = 67108864
        opts.max_write_buffer_number = 3
        opts.target_file_size_base = 67108864

        opts.table_factory = rocksdb.BlockBasedTableFactory(
            filter_policy=rocksdb.BloomFilterPolicy(10),
            block_cache=rocksdb.LRUCache(2 * (1024**3)),
            block_cache_compressed=rocksdb.LRUCache(500 * (1024**2)),
        )

        if not filename:
            if "BASE_PATH" in os.environ:
                self.filename = f"{os.environ['BASE_PATH']}/database/smt.db"
            else:
                Path("./database").mkdir(parents=True, exist_ok=True)
                self.filename = "./database/smt.db"
        else:
            self.filename = filename

        self.db = rocksdb.DB(self.filename, opts)
        self.batch = rocksdb.WriteBatch()

    async def set(self, key: bytes, value: bytes) -> None:
        self.batch.put(key, value)

    async def get(self, key: bytes) -> bytes:
        return self.db.get(key)

    async def delete(self, key: bytes) -> None:
        self.db.delete(key)

    async def write(self) -> None:
        self.db.write(self.batch)
        self.batch = rocksdb.WriteBatch()
