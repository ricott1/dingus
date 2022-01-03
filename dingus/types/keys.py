from __future__ import annotations

import os 
import hashlib
import pyaes
import json
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder, HexEncoder

import dingus.constants as constants
import dingus.utils as utils


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
    def from_json(cls, filename: str, password: str = "") -> PrivateKey:
        with open(f"dingus/accounts/{filename}", "r") as f:
            cipherdata = json.loads(f.read())
    
        ciphertext = bytes.fromhex(cipherdata["ciphertext"])
        salt = bytes.fromhex(cipherdata["salt"])
        iv = bytes.fromhex(cipherdata["iv"])
        iteration_count = cipherdata["iteration_count"]
        key = hashlib.pbkdf2_hmac('sha256', str.encode(password), salt, iteration_count)
        
        # Decryption with AES-256-CBC
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        decryptedData = decrypter.feed(ciphertext)
        decryptedData += decrypter.feed()
        return PrivateKey(decryptedData)

    def __init__(self, source) -> None:
        super().__init__(source)
    
    def to_public_key(self) -> PublicKey:
        return PublicKey(self.verify_key._key)
    
    def to_json(self, password: str = "", iteration_count: int = 1000000) -> None:
        salt = os.urandom(8)
        iv = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', str.encode(password), salt, iteration_count)

        # Encryption with AES-256-CBC
        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        ciphertext = encrypter.feed(self.encode())
        ciphertext += encrypter.feed()


        cipherdata = {
                "ciphertext": ciphertext.hex(),
                "salt": salt.hex(),
                "iv": iv.hex(),
                "iteration_count": iteration_count,
                "public_key": self.to_public_key().encode().hex()
        }
        filename = f"{self.to_public_key().to_address().to_lsk32()}.json"
        with open(f"dingus/accounts/{filename}", "w") as f:
            f.write(json.dumps(cipherdata))


