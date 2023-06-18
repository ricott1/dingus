from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import dingus.types.keys as keys
    AccountType = str | int | keys.PublicKey | bool

import json
import logging
import os


class InvalidAccountFileError(Exception):
    pass

@dataclass
class Account(object):
    address: str
    name: str
    balance: int
    public_key: keys.PublicKey
    nonce: int
    ciphertext: str
    salt: str
    iv: str
    iteration_count: int
    bookmark: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, AccountType]) -> Account:
        if "public_key" in data:
            if type(data["public_key"]) == str:
                data["public_key"] = keys.PublicKey(bytes.fromhex(data["public_key"]))
            elif type(data["public_key"]) == bytes:
                data["public_key"] = keys.PublicKey(data["public_key"])

        # fill in missing fields with default values
        if "nonce" not in data:
            data["nonce"] = 0
        if "balance" not in data:
            data["balance"] = 0
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
        # _dict: dict[str, AccountType] = {**vars(self).items()}
        _dict = {
            "address": self.address,
            "name": self.name,
            "balance": self.balance,
            "public_key": self.public_key,
            "nonce": self.nonce,
            "ciphertext": self.ciphertext,
            "salt": self.salt,
            "iv": self.iv,
            "iteration_count": self.iteration_count,
            "bookmark": self.bookmark
        }
        if self.public_key:
            _dict["public_key"] = self.public_key.to_bytes().hex()

        return _dict

    def save(self, filename: str) -> None:
        try:
            with open(f"{os.environ['BASE_PATH']}/accounts/{filename}", "w") as f:
                f.write(json.dumps(self.to_dict()))
        except Exception as err:
            logging.error(f"utils.save_account {err}")
            raise err
