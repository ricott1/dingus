from __future__ import annotations

import os 

import dingus.constants as constants
import dingus.utils as utils
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder, HexEncoder


class Address(bytes):
    def __init__(self, source) -> None:
        assert len(self) == constants.ADDRESS_LENGTH, "Invalid address length."
    
    @property
    def to_lsk_format(self) -> str:
        return "lsk..."

class PublicKey(VerifyKey):
    def to_address(self) -> Address:
        return Address(utils.hash(self.encode())[:20])

class PrivateKey(SigningKey):
    @classmethod
    def from_passphrase(cls, passphrase: str) -> PrivateKey:
        return utils.passphrase_to_sk(passphrase)
    
    @classmethod
    def from_json(cls, filename: str) -> PrivateKey:
        with open(f"dingus/accounts/{filename}", "r") as f:
            _key_hex = f.read()
        return PrivateKey(bytes.fromhex(_key_hex))

    def __init__(self, source) -> None:
        super().__init__(source)
    
    def to_public_key(self) -> PublicKey:
        return PublicKey(self.verify_key._key)
    
    def to_json(self) -> None:
        filename = f"{self.to_public_key().to_address().hex()}.json"
        _key_hex = self.encode().hex()
        with open(f"dingus/accounts/{filename}", "w") as f:
            f.write(_key_hex)


