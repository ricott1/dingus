from __future__ import annotations

import os
import hashlib
import pyaes
import json
from nacl.signing import SigningKey, VerifyKey

import dingus.constants as constants
import dingus.utils as utils
import dingus.crypto as crypto
import hmac, hashlib


class Address(bytes):
    def __init__(self, source) -> None:
        assert len(self) == constants.Length.ADDRESS, "Invalid address length."
        super().__init__()

    def to_lsk32(self) -> str:
        return utils.address_to_lisk32(self)
    
    def to_bytes(self) -> bytes:
        return bytes(self)


class PublicKey(bytes, VerifyKey):
    def to_address(self) -> Address:
        return Address(crypto.hash(self.encode())[:20])

    def to_bytes(self) -> bytes:
        return bytes(self)


class PrivateKey(bytes, SigningKey):
    DEFAULT_DERIVATION_PATH = [44 + 0x80000000, 134 + 0x80000000, 0x80000000]

    @classmethod
    def from_dict(cls, data: dict, password: str = "") -> PrivateKey:
        ciphertext = bytes.fromhex(data["ciphertext"])
        salt = bytes.fromhex(data["salt"])
        iv = bytes.fromhex(data["iv"])
        iteration_count = data["iteration_count"]
        key = hashlib.pbkdf2_hmac("sha256", str.encode(password), salt, iteration_count)

        # Decryption with AES-256-CBC
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        decryptedData = decrypter.feed(ciphertext)
        decryptedData += decrypter.feed()
        return PrivateKey(decryptedData)

    @classmethod
    def from_file(cls, filename: str, password: str = "") -> PrivateKey:
        with open(f"{os.environ['BASE_PATH']}/accounts/{filename}", "r") as f:
            data = json.loads(f.read())

        return PrivateKey.from_dict(data, password)

    @classmethod
    def random(cls) -> PrivateKey:
        return PrivateKey(os.urandom(32))

    @classmethod
    def from_passphrase(cls, passphrase: str, path: list[int] = DEFAULT_DERIVATION_PATH, pwd: str = "") -> PrivateKey:
        masterSeed = crypto.passphrase_to_seed(passphrase, password=pwd)

        sign = hmac.new('ed25519 seed'.encode('utf-8'), masterSeed, hashlib.sha512).digest()
        node = {
            "key": sign[:32],
            "chainCode": sign[32:]
        }
        for index in path:
            indexBuffer = index.to_bytes(4, byteorder='big')
            sign = hmac.new(node["chainCode"], b"\x00" + node["key"] + indexBuffer, hashlib.sha512).digest()
            node = {
                "key": sign[:32],
                "chainCode": sign[32:]
            }

        return PrivateKey(node["key"])

    def __init__(self, source) -> None:
        super().__init__(source)

    def to_public_key(self) -> PublicKey:
        return PublicKey(self.verify_key._key)

    def to_bytes(self) -> bytes:
        return bytes(self)

    def encrypt(self, password: str = "", iteration_count: int = 1000000) -> dict:
        salt = os.urandom(8)
        iv = os.urandom(16)
        key = hashlib.pbkdf2_hmac("sha256", str.encode(password), salt, iteration_count)
        # key = nacl.pwhash.argon2id.kdf(size, password, salt)

        # Encryption with AES-256-CBC
        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        ciphertext = encrypter.feed(self.encode())
        ciphertext += encrypter.feed()
        data = {
            "ciphertext": ciphertext.hex(),
            "salt": salt.hex(),
            "iv": iv.hex(),
            "iteration_count": iteration_count,
        }

        return data



EMPTY_KEY = PublicKey(b"0" * constants.Length.EDSA_PUBLIC_KEY)
INVALID_BLS_KEY = b"\00" * 48

if __name__ == "__main__":
    pub_key = PublicKey(bytes.fromhex("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"))
    print(pub_key.to_address().to_lsk32())
    print(pub_key)
    passphrase="economy cliff diamond van multiply general visa picture actor teach cruel tree adjust quit maid hurry fence peace glare library curve soap cube must"
    path = [44 + 0x80000000, 134 + 0x80000000, 4 + 0x80000000]
    sphrase="target cancel solution recipe vague faint bomb convince pink vendor fresh patrol"
    path = [44 + 0x80000000, 134 + 0x80000000, 0 + 0x80000000]
    print(path)
    print(PrivateKey.from_passphrase(passphrase, path, "TREZOR").to_public_key().hex())
    