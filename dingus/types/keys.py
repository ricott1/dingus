from __future__ import annotations

import os 
import hashlib
import pyaes
import json
from nacl.signing import SigningKey, VerifyKey

import dingus.constants as constants
import dingus.utils as utils


class Address(bytes):
    def __init__(self, source) -> None:
        assert len(self) == constants.ADDRESS_LENGTH, "Invalid address length."
        super().__init__()
    
    def to_lsk32(self) -> str:
        return utils.address_to_lisk32(self)

class PublicKey(VerifyKey):
    def to_address(self) -> Address:
        return Address(utils.hash(self.encode())[:20])
    
    def hexbytes(self) -> bytes:
        return bytes(self)

class PrivateKey(SigningKey):
    @classmethod
    def from_passphrase(cls, passphrase: str) -> PrivateKey:
        return utils.passphrase_to_private_key(passphrase)
    
    @classmethod
    def from_json(cls, data: dict, password: str = "") -> PrivateKey:
        ciphertext = bytes.fromhex(data["ciphertext"])
        salt = bytes.fromhex(data["salt"])
        iv = bytes.fromhex(data["iv"])
        iteration_count = data["iteration_count"]
        key = hashlib.pbkdf2_hmac('sha256', str.encode(password), salt, iteration_count)

        # Decryption with AES-256-CBC
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        decryptedData = decrypter.feed(ciphertext)
        decryptedData += decrypter.feed()
        return PrivateKey(decryptedData)

    @classmethod
    def from_file(cls, filename: str, password: str = "") -> PrivateKey:
        with open(f"{os.environ['BASE_PATH']}/accounts/{filename}", "r") as f:
            data = json.loads(f.read())
            
        return PrivateKey.from_json(data, password)

    def __init__(self, source) -> None:
        super().__init__(source)
    
    def to_public_key(self) -> PublicKey:
        return PublicKey(self.verify_key._key)
    
    def hexbytes(self) -> bytes:
        return bytes(self)
    
    def encrypt(self, password: str = "", iteration_count: int = 1000000) -> dict:
        salt = os.urandom(8)
        iv = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', str.encode(password), salt, iteration_count)
        # key = nacl.pwhash.argon2id.kdf(size, password, salt)

        # Encryption with AES-256-CBC
        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        ciphertext = encrypter.feed(self.encode())
        ciphertext += encrypter.feed()
        data = {
                "ciphertext": ciphertext.hex(),
                "salt": salt.hex(),
                "iv": iv.hex(),
                "iteration_count": iteration_count
        }

        return data


EMPTY_KEY = PublicKey(b"0"*constants.EDSA_PUBLIC_KEY_LENGTH)