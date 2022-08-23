from __future__ import annotations
import logging

import dingus.codec as codec
import dingus.utils as utils
import dingus.network.api as api
from dingus.constants import (
    SIGNATURE_TAG_TRANSACTION,
    ADDRESS_LENGTH,
    BALANCE_TRANSFER_MAX_DATA_LENGTH,
    EDSA_SIGNATURE_LENGTH,
    EDSA_PUBLIC_KEY_LENGTH,
)
from dingus.codec.json_format import MessageToDict
from nacl.signing import SigningKey

import os
import json


class Transaction(object):
    def __init__(self, params: dict) -> None:
        self.schema = codec.transaction.Transaction()
        for k, v in params.items():
            # paramsis handled separately
            if k == "params":
                continue

            # signatures cannot be set directly
            if k == "signatures":
                continue

            setattr(self.schema, k, v)

        if "signatures" in params:
            for signature in params["signatures"]:
                self.schema.signatures.extend([signature])

        self.params= module_params_to_schema[
            f"{params['module']}/{params['command']}"
        ].from_dict(params["params"])
        self.schema.params= self.params.bytes
        self.unsigned_bytes = self.schema.SerializeToString()

        if "MIN_FEE_PER_BYTE" in os.environ:
            min_fee_per_byte = int(os.environ["MIN_FEE_PER_BYTE"])
        else:
            min_fee_per_byte = 0

        assert self.fee >= self.params.base_fee + min_fee_per_byte * (
            len(self.unsigned_bytes) + EDSA_SIGNATURE_LENGTH
        ), "Invalid 'fee'."

    @classmethod
    def validate_parameters(cls, params: dict) -> None:
        assert "module" in params, "Missing 'module' parameter."
        assert (
            f"{params['module']}/{params['command']}" in module_params_to_schema
        ), "Invalid 'module/command' combination."
        assert "command" in params, "Missing 'command' parameter."
        assert "senderPublicKey" in params, "Missing 'senderPublicKey' parameter."
        assert (
            len(params["senderPublicKey"]) == EDSA_PUBLIC_KEY_LENGTH
        ), "Invalid 'senderPublicKey' length."
        assert "nonce" in params, "Missing 'nonce' parameter."
        assert params["nonce"] >= 0, "Invalid 'nonce'."
        assert "fee" in params, "Missing 'fee' parameter."
        assert params["fee"] >= 0, "Invalid 'fee'."
        assert "params" in params, "Missing 'params' parameter."

    @classmethod
    def from_dict(cls, params: dict) -> Transaction:
        cls.validate_parameters(params)
        return Transaction(params)

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
        return utils.hash(self.bytes)

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
        signature = utils.sign(utils.hash(SIGNATURE_TAG_TRANSACTION + net_id + self.unsigned_bytes), sk)
        self.schema.signatures.extend([signature])

    def send(self) -> dict:
        assert self.is_signed, "Cannot send unsigned transaction."
        return api.send_transaction(self.bytes.hex())

    def __str__(self) -> str:
        return json.dumps(self.to_dict)


class Asset(object):
    @classmethod
    def from_dict(cls, params: dict) -> Asset:
        cls.validate_parameters(params)
        return cls(params)

    @classmethod
    def validate_parameters(cls, params: dict) -> None:
        pass

    @property
    def bytes(self) -> bytes:
        return self.schema.SerializeToString()


class BalanceTransferParams(Asset):
    def __init__(self, params: dict = {}) -> None:
        self.schema = codec.token_balance_transfer_params.BalanceTransferParams()
        self.base_fee = 0
        for k, v in params.items():
            setattr(self.schema, k, v)

    @classmethod
    def validate_parameters(cls, params: dict) -> None:
        assert "amount" in params, "Missing 'amount' paramsproperty."
        assert params["amount"] > 0, "Invalid 'amount' params property."
        assert (
            "recipientAddress" in params
        ), "Missing 'recipientAddress' params property."
        assert (
            len(params["recipientAddress"]) == ADDRESS_LENGTH
        ), "Invalid 'recipientAddress' params property."
        assert "data" in params, "Missing 'data' params property."
        assert (
            len(params["data"]) < BALANCE_TRANSFER_MAX_DATA_LENGTH
        ), f"'data' params property exceeds maximum length ({len(params['data'])} > {BALANCE_TRANSFER_MAX_DATA_LENGTH})."

    @property
    def amount(self) -> int:
        return self.schema.amount

    @property
    def recipientAddress(self) -> bytes:
        return self.schema.recipientAddress

    @property
    def data(self) -> str:
        return self.schema.data


module_params_to_schema = {"token/transfer": BalanceTransferParams}
