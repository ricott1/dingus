from __future__ import annotations

from dataclasses import dataclass
import dingus.types.keys as keys
import json
import logging
import os

AccountType = str | int | keys.PublicKey | bool

class InvalidAccountFileError(Exception):
    pass

@dataclass
class Account(object):
    address: str = ""
    name: str = ""
    balance: int = 0
    public_key: keys.PublicKey = keys.EMPTY_KEY
    nonce: int = 0
    ciphertext: str = ""
    salt: str = ""
    iv: str = ""
    iteration_count: int = 0
    bookmark: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, AccountType]) -> Account:
        if "public_key" in data:
            if type(data["public_key"]) == str:
                data["public_key"] = keys.PublicKey(bytes.fromhex(data["public_key"]))
            elif type(data["public_key"]) == bytes:
                data["public_key"] = keys.PublicKey(data["public_key"])

        return Account(**data)

    @classmethod
    def from_file(cls, filename: str) -> Account:
        try:
            with open(f"{os.environ['BASE_PATH']}/accounts/{filename}", "r") as f:
                data: dict = json.load(f)
        except Exception as err:
            logging.error(f"utils.load_account {err}")
            raise err

        if "address" not in data:
            logging.error(f"utils.load_account Missing address")
            raise InvalidAccountFileError
        
        return Account.from_dict(data)
    
    def to_dict(self) -> dict[str, AccountType]:
        _dict: dict[str, AccountType] = {**vars(self).items()}
        if self.public_key:
            _dict["public_key"] = self.public_key.hexbytes().hex()
        
        return _dict
    
    def save(self, filename: str) -> None:
        try:
            with open(f"{os.environ['BASE_PATH']}/accounts/{filename}", "w") as f:
                f.write(json.dumps(self.to_dict()))
        except Exception as err:
            logging.error(f"utils.save_account {err}")
            raise err

