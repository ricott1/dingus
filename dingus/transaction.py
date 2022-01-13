from __future__ import annotations
import logging
from posix import environ

import dingus.codec as codec
import dingus.utils as utils
import dingus.network.api as api
from dingus.constants import LSK, ADDRESS_LENGTH, BALANCE_TRANSFER_MAX_DATA_LENGTH, EDSA_SIGNATURE_LENGTH, EDSA_PUBLIC_KEY_LENGTH
from dingus.codec.json_format import MessageToDict
from google.protobuf.reflection import GeneratedProtocolMessageType
from nacl.signing import SigningKey

import os
import json


class Transaction(object):
    def __init__(self, params: dict) -> None:
        self.schema = codec.base_transaction.Transaction()
        for k, v in params.items():
            # asset is handled separately
            if k == "asset": 
                continue
            
            # signatures cannot be set directly
            if k == "signatures": 
                continue

            setattr(self.schema, k, v)

        if "signatures" in params:
            for signature in params["signatures"]:
                self.schema.signatures.extend([signature])
            
        self.asset = module_asset_to_schema[f"{params['moduleID']}:{params['assetID']}"].fromDict(params["asset"])
        self.schema.asset = self.asset.bytes
        self.unsigned_bytes = self.schema.SerializeToString()

        if "MIN_FEE_PER_BYTE" in os.environ:
            min_fee_per_byte = int(os.environ["MIN_FEE_PER_BYTE"])
        else:
            min_fee_per_byte = 0

        assert self.fee >= self.asset.base_fee + min_fee_per_byte * (len(self.unsigned_bytes) + EDSA_SIGNATURE_LENGTH), "Invalid 'fee'."

    @classmethod
    def validate_parameters(cls, params:dict) -> None:
        assert "moduleID" in params, "Missing 'moduleID' parameter."
        assert f"{params['moduleID']}:{params['assetID']}" in module_asset_to_schema, "Invalid 'moduleID:assetID' combination."
        assert "assetID" in params, "Missing 'assetID' parameter."
        assert "senderPublicKey" in params, "Missing 'senderPublicKey' parameter."
        assert len(params["senderPublicKey"]) == EDSA_PUBLIC_KEY_LENGTH, "Invalid 'senderPublicKey' length."
        assert "nonce" in params, "Missing 'nonce' parameter."
        assert params["nonce"] >= 0, "Invalid 'nonce'."
        assert "fee" in params, "Missing 'fee' parameter."
        assert params["fee"] >= 0, "Invalid 'fee'."
        assert "asset" in params, "Missing 'asset' parameter."

    @classmethod
    def from_json(cls, json_string: str) -> Transaction:
        return cls.fromDict(json_string.json())

    @classmethod
    def fromDict(cls, params: dict) -> Transaction:
        cls.validate_parameters(params)
        return Transaction(params)

    @property
    def moduleID(self) -> int:
        return self.schema.moduleID

    @property
    def assetID(self) -> int:
        return self.schema.assetID
    
    @property
    def senderPublicKey(self) -> bytes:
        return self.schema.senderPublicKey
    
    @property
    def nonce(self) -> int:
        return self.schema.nonce
    
    @property
    def fee(self) -> int:
        return self.schema.fee
    
    @property
    def signatures(self) -> int:
        return self.schema.signatures

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()
    
    @property
    def to_dict(self) -> dict:
        base_tx = MessageToDict(self.schema)
        base_tx["asset"] = MessageToDict(self.schema)
        return base_tx

    @property
    def id(self) -> bytes:
        return utils.hash(self.bytes)
    
    @property
    def is_signed(self) -> bool:
        return len(self.schema.signatures) > 0

    def sign(self, sk: SigningKey) -> None:
        if len(self.signatures) != 0:
            logging.warn("Transaction already signed.")
            return

        if "NETWORK_ID" not in os.environ:
            logging.warning("Cannot sign transaction, network ID not set.")
            return

        net_id = bytes.fromhex(os.environ["NETWORK_ID"])
        signature = utils.sign(net_id + self.unsigned_bytes, sk)
        self.schema.signatures.extend([signature])
    
    def send(self) -> dict:
        assert self.is_signed, "Cannot send unsigned transaction."
        return api.send_transaction(self.bytes.hex())
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict)


class Asset(object):

    @classmethod
    def fromDict(cls, params: dict) -> Asset:
        cls.validate_parameters(params)
        return cls(params)
    
    @classmethod
    def from_json(cls, json_string: str) -> Asset:
        return cls.fromDict(json_string.json())

    @classmethod
    def validate_parameters(cls, params:dict) -> None:
        pass

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()


class BalanceTransferAsset(Asset):
    def __init__(self, params: dict = {}) -> None:
        self.schema = codec.token_balance_transfer_asset.BalanceTransferAsset()
        self.base_fee = 0
        for k, v in params.items():
            setattr(self.schema, k, v)

    @classmethod
    def validate_parameters(cls, params:dict) -> None:
        assert "amount" in params, "Missing 'amount' asset parameter."
        assert params["amount"] > 0, "Invalid 'amount' asset parameter."
        assert "recipientAddress" in params, "Missing 'recipientAddress' asset parameter."
        assert len(params["recipientAddress"]) == ADDRESS_LENGTH, "Invalid 'recipientAddress' asset parameter." 
        assert "data" in params, "Missing 'data' asset parameter."     
        assert len(params["data"]) < BALANCE_TRANSFER_MAX_DATA_LENGTH, f"'data' asset parameter exceeds maximum length ({len(params['data'])} > {BALANCE_TRANSFER_MAX_DATA_LENGTH})."

    @property
    def amount(self) -> int:
        return self.schema.amount
    
    @property
    def recipientAddress(self) -> bytes:
        return self.schema.recipientAddress
    
    @property
    def data(self) -> str:
        return self.schema.data

module_asset_to_schema = {
    "2:0" : BalanceTransferAsset
}