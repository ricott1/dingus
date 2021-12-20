from __future__ import annotations

import dingus.constants as constants
import dingus.utils as utils
from nacl.signing import SigningKey, VerifyKey

class Address(bytes):
    def __init__(self, source) -> None:
        assert len(self) == constants.ADDRESS_LENGTH, "Invalid address length."
    
    @property
    def to_lsk_format(self) -> str:
        return "lsk..."

class PublicKey(VerifyKey):
    def __init__(self, source) -> None:
        super().__init__(source)
    
    def to_address(self) -> Address:
        return Address(utils.hash(self)[:20])

class PrivateKey(SigningKey):
    @classmethod
    def from_passphrase(cls, passphrase: str) -> PrivateKey:
        return utils.passphrase_to_sk(passphrase)

    def __init__(self, source) -> None:
        super().__init__(source)
    
    def to_public_key(self) -> PublicKey:
        return PublicKey(self.verify_key._key)