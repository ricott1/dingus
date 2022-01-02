from __future__ import annotations

import os 

import dingus.constants as constants
import dingus.utils as utils
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder, HexEncoder


class Address(bytes):
    def __init__(self, source) -> None:
        assert len(self) == constants.ADDRESS_LENGTH, "Invalid address length."
    
    def to_lsk32(self) -> str:
        return utils.address_to_lisk32(self)
    
    def to_avatar(self) -> list[tuple[int]]:
        avatar = []
        r, g, b = [utils.hash(bytes.fromhex(f"0{i}") + self) for i in range(3)]
        for i in range(0, len(r), 2):
            _r = int.from_bytes(r[i:i+1], "big")//16*16
            _g = int.from_bytes(g[i:i+1], "big")//16*16
            _b = int.from_bytes(b[i:i+1], "big")//16*16
            avatar.append((_r, _g, _b))
        return avatar

class PublicKey(VerifyKey):
    def to_address(self) -> Address:
        return Address(utils.hash(self.encode())[:20])

class PrivateKey(SigningKey):
    @classmethod
    def from_passphrase(cls, passphrase: str) -> PrivateKey:
        return utils.passphrase_to_private_key(passphrase)
    
    @classmethod
    def from_json(cls, filename: str) -> PrivateKey:
        with open(f"dingus/accounts/{filename}", "br") as f:
            key_bytes = f.read()
        return PrivateKey(key_bytes)

    def __init__(self, source) -> None:
        super().__init__(source)
    
    def to_public_key(self) -> PublicKey:
        return PublicKey(self.verify_key._key)
    
    def to_json(self) -> None:
        filename = f"{self.to_public_key().to_address().hex()}.json"
        with open(f"dingus/accounts/{filename}", "bw") as f:
            f.write(self.encode())


