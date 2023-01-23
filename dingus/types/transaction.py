from __future__ import annotations
import logging
from typing import Any

import dingus.codec as codec
import dingus.utils as utils
import dingus.crypto as crypto
import dingus.network.api as api
from dingus.constants import Length, SignatureTags
from dingus.codec.json_format import MessageToDict
from nacl.signing import SigningKey

from google.protobuf.reflection import GeneratedProtocolMessageType

import os
import json


class Transaction(object):
    def __init__(self, properties: dict) -> None:
        self.schema = codec.transaction.Transaction()
        for k, v in properties.items():
            # paramsis handled separately
            if k == "params":
                continue

            # signatures cannot be set directly
            if k == "signatures":
                continue

            setattr(self.schema, k, v)

        if "signatures" in properties:
            for signature in properties["signatures"]:
                self.schema.signatures.extend([signature])

        self.params= module_params_to_schema[
            f"{properties['module']}:{properties['command']}"
        ].from_dict(properties["params"])
        self.schema.params= self.params.bytes
        self.unsigned_bytes = self.schema.SerializeToString()

        if "MIN_FEE_PER_BYTE" in os.environ:
            min_fee_per_byte = int(os.environ["MIN_FEE_PER_BYTE"])
        else:
            min_fee_per_byte = 0

        assert self.fee >= min_fee_per_byte * (
            len(self.unsigned_bytes) + Length.EDSA_SIGNATURE
        ), "Invalid 'fee'."

    @classmethod
    def validate_schema(cls, properties: dict) -> None:
        assert "module" in properties, "Missing 'module' parameter."
        assert (
            f"{properties['module']}:{properties['command']}" in module_params_to_schema
        ), "Invalid 'module/command' combination."
        assert "command" in properties, "Missing 'command' parameter."
        assert "senderPublicKey" in properties, "Missing 'senderPublicKey' parameter."
        assert (
            len(properties["senderPublicKey"]) == Length.EDSA_PUBLIC_KEY
        ), "Invalid 'senderPublicKey' length."
        assert "nonce" in properties, "Missing 'nonce' parameter."
        assert properties["nonce"] >= 0, "Invalid 'nonce'."
        assert "fee" in properties, "Missing 'fee' parameter."
        assert properties["fee"] >= 0, "Invalid 'fee'."
        assert "params" in properties, "Missing 'params' parameter."

    @classmethod
    def from_dict(cls, properties: dict) -> Transaction:
        cls.validate_schema(properties)
        return Transaction(properties)

    @property
    def module(self) -> bytes:
        return self.schema.module

    @property
    def command(self) -> bytes:
        return self.schema.command

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
    def signatures(self) -> list[bytes]:
        return self.schema.signatures

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()

    @property
    def to_dict(self) -> dict:
        base_tx = MessageToDict(self.schema)
        base_tx["params"] = MessageToDict(self.params.schema)
        return base_tx

    @property
    def id(self) -> bytes:
        return crypto.hash(self.bytes)

    @property
    def is_signed(self) -> bool:
        return len(self.schema.signatures) > 0

    def sign(self, sk: SigningKey) -> None:
        # if len(self.signatures) != 0:
        #     logging.warn("Transaction already signed.")
        #     return

        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot sign transaction, network ID not set.")
            return

        net_id = bytes.fromhex(os.environ["CHAIN_ID"])
        signature = crypto.sign(crypto.hash(SignatureTags.TRANSACTION + net_id + self.unsigned_bytes), sk)
        self.schema.signatures.extend([signature])

    def send(self) -> dict:
        assert self.is_signed, "Cannot send unsigned transaction."
        return api.send_transaction(self.bytes.hex())

    def __str__(self) -> str:
        return json.dumps(self.to_dict)


class Params(object):
    def __init__(self, schema: GeneratedProtocolMessageType, properties: dict[str, Any]) -> None:
        self.schema = schema
        for k, v in properties.items():
            try:
                setattr(self.schema, k, v)
            except AttributeError:
                getattr(self.schema, k).extend(v)

    @classmethod
    def from_dict(cls, params: dict) -> Params:
        cls.validate_schema(params)
        return cls(params)

    @classmethod
    def validate_schema(cls, properties: dict) -> None:
        pass

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()


class BalanceTransferParams(Params):
    def __init__(self, properties: dict[str, Any]) -> None:
        super().__init__(codec.transaction.BalanceTransferParams(), properties)

    @classmethod
    def validate_schema(cls, properties: dict) -> None:
        assert "amount" in properties, "Missing 'amount' paramsproperty."
        assert properties["amount"] > 0, "Invalid 'amount' params property."
        assert (
            "recipientAddress" in properties
        ), "Missing 'recipientAddress' params property."
        assert (
            len(properties["recipientAddress"]) == Length.ADDRESS
        ), "Invalid 'recipientAddress' params property."
        assert "data" in properties, "Missing 'data' params property."
        assert (
            len(properties["data"]) < Length.BALANCE_TRANSFER_MAX_DATA
        ), f"'data' params property exceeds maximum length ({len(properties['data'])} > {Length.BALANCE_TRANSFER_MAX_DATA})."

    @property
    def amount(self) -> int:
        return self.schema.amount

    @property
    def recipientAddress(self) -> bytes:
        return self.schema.recipientAddress

    @property
    def data(self) -> str:
        return self.schema.data


class SidechainRegistrationParams(Params):
    def __init__(self, properties: dict[str, Any]) -> None:
        self.schema = codec.transaction.SidechainRegistrationParams()
        self.schema.name = properties["name"]
        self.schema.chainID = properties["chainID"]
        for validator in properties["sidechainValidators"]:
            self.schema.sidechainValidators.extend(
                [
                    codec.transaction.ChainValidator(
                        blsKey=validator["blsKey"], bftWeight=validator["bftWeight"]
                    )
                ]
            )
        self.schema.sidechainCertificateThreshold = properties["sidechainCertificateThreshold"]

class MainchainRegistrationParams(Params):
    def __init__(self, properties: dict[str, Any]) -> None:
        self.schema = codec.transaction.MainchainRegistrationParams()
        self.schema.ownName = properties["ownName"]
        self.schema.ownChainID = properties["ownChainID"]
        for validator in properties["mainchainValidators"]:
            self.schema.mainchainValidators.extend(
                [
                    codec.transaction.ChainValidator(
                        blsKey=validator["blsKey"], bftWeight=validator["bftWeight"]
                    )
                ]
            )
        self.schema.mainchainCertificateThreshold = properties["mainchainCertificateThreshold"]
        self.schema.signature = properties["signature"]
        self.schema.aggregationBits = properties["aggregationBits"]


module_params_to_schema = {
    "token:transfer": BalanceTransferParams,
    "interoperability:registerSidechain": SidechainRegistrationParams,
    "interoperability:registerMainchain": MainchainRegistrationParams,
    }
