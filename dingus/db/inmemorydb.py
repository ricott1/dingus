from __future__ import annotations

class InMemoryDB(object):
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
    
    async def write(self) -> None:
        pass

