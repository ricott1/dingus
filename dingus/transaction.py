from __future__ import annotations
import logging

import dingus.codec as codec
import dingus.utils as utils
import dingus.network.api as api
import dingus.constants as constants
from dingus.constants import LSK, ADDRESS_LENGTH, BALANCE_TRANSFER_MAX_DATA_LENGTH
from dingus.codec.json_format import MessageToDict
from google.protobuf.reflection import GeneratedProtocolMessageType
from nacl.signing import SigningKey

import os
import json



class Transaction(object):
    MODULE_ID = 0
    ASSET_ID = 0

    def __init__(self, senderPublicKey : bytes, nonce:int, fee:int, asset_schema: GeneratedProtocolMessageType, asset: dict) -> None:
        assert len(senderPublicKey) == 32, "Invalid 'senderPublicKey' length."
        assert nonce >= 0, "Invalid 'nonce'."
        assert fee >= 0, "Invalid 'fee'."
        
        self.schema = codec.base_transaction.Transaction()
        self.schema.moduleID = self.MODULE_ID
        self.schema.assetID = self.ASSET_ID
        self.schema.senderPublicKey = senderPublicKey
        self.schema.nonce = nonce
        self.schema.fee = fee
        self.signatures = []

        self.asset_schema = asset_schema
        for k, v in asset.items():
            setattr(self.asset_schema, k, v)

        self.schema.asset = self.asset_schema.SerializeToString()
        self.unsigned_bytes = self.schema.SerializeToString()
    
    @property
    def moduleID(self) -> int:
        return self.schema.moduleID
    @moduleID.setter
    def moduleID(self, value: int) -> None:
        self.schema.moduleID = value
    
    @property
    def assetID(self) -> int:
        return self.schema.assetID
    @assetID.setter
    def assetID(self, value: int) -> None:
        self.schema.assetID = value
    
    @property
    def senderPublicKey(self) -> bytes:
        return self.schema.senderPublicKey
    @senderPublicKey.setter
    def senderPublicKey(self, value: bytes) -> None:
        self.schema.senderPublicKey = value
    
    @property
    def nonce(self) -> int:
        return self.schema.nonce
    @nonce.setter
    def nonce(self, value: int) -> None:
        self.schema.nonce = value
    
    @property
    def fee(self) -> int:
        return self.schema.fee
    @fee.setter
    def fee(self, value: int) -> None:
        self.schema.fee = value

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()
    
    @property
    def dict(self) -> dict:
        base_tx = MessageToDict(self.schema)
        base_tx["asset"] = MessageToDict(self.asset_schema)
        return base_tx

    @property
    def id(self) -> bytes:
        return utils.hash(self.bytes)
    
    @property
    def signed(self) -> bool:
        return len(self.schema.signatures) > 0

    def sign(self, sk: SigningKey) -> None:
        if "DINGUS_NETWORK_ID" not in os.environ:
            logging.warning("Cannot sign transaction, network ID not set.")
            return
        net_id = bytes.fromhex(os.environ["DINGUS_NETWORK_ID"])
        signature = utils.sign(net_id + self.unsigned_bytes, sk)
        self.schema.signatures.extend([signature])
    
    def send(self) -> dict:
        return api.send_transaction(self.bytes.hex())
    
    def __str__(self) -> str:
        return json.dumps(self.dict)


class BalanceTransfer(Transaction):
    MODULE_ID = 2
    ASSET_ID = 0

    @classmethod
    def from_json(cls, json_string: str) -> BalanceTransfer:
        return cls.fromDict(json_string.json())

    @classmethod
    def fromDict(cls, params: dict) -> BalanceTransfer:
        assert "senderPublicKey" in params, "Missing 'senderPublicKey' parameter."
        assert "nonce" in params, "Missing 'nonce' parameter."
        assert "fee" in params, "Missing 'fee' parameter."
        assert "asset" in params, "Missing 'asset' parameter."
        
        assert "amount" in params["asset"], "Missing 'amount' asset parameter."
        assert "recipientAddress" in params["asset"], "Missing 'recipientAddress' asset parameter."
        assert "data" in params["asset"], "Missing 'data' asset parameter."
        assert len(params["asset"]["data"]) < BALANCE_TRANSFER_MAX_DATA_LENGTH, "Invalid 'data' asset parameter."
        assert params["asset"]["amount"] > 0, "Invalid 'amount' asset parameter."
        assert len(params["asset"]["recipientAddress"]) == ADDRESS_LENGTH, "Invalid 'recipientAddress' asset parameter."
        
        return BalanceTransfer(params["senderPublicKey"], params["nonce"], params["fee"], params["asset"])
        

    def __init__(self, senderPublicKey : bytes, nonce:int, fee:int, asset: dict) -> None:
        super().__init__(senderPublicKey, nonce, fee, codec.token_balance_transfer_asset.BalanceTransferAsset(), asset)


if __name__ == "__main__":

    print(len(bytes.fromhex("c3c78ef27a9cf7937c09ee4e4ea49aabdaf6bbf5f48d21df35b9d26347729e10")))
    params = {
        "senderPublicKey": utils.random_public_key().encode(),
        "nonce": 0,
        "fee": int(0.5 * LSK),
        "asset": {
            "amount": int(3 * LSK),
            "recipientAddress": utils.random_address(),
            "data": ""
        }   
    }

    trs = BalanceTransfer.fromDict(params)
    trs.nonce=166
    
    passphrase = "peanut hundred pen hawk invite exclude brain chunk gadget wait wrong ready"
    trs.sign(utils.passphrase_to_private_key(passphrase))
    print(trs)
    # trs.send()