from __future__ import annotations
from typing import Any

import dingus.codec as codec
import dingus.utils as utils
import dingus.crypto as crypto
from dingus.constants import (
    CHAIN_ID_LENGTH,
    TOKEN_ID_LENGTH,
)
from dingus.codec.json_format import MessageToDict

from google.protobuf.reflection import GeneratedProtocolMessageType
import json

class CCM(object):
    def __init__(self, properties: dict) -> None:
        self.schema = codec.ccm.CCM()
        for k, v in properties.items():
            # params is handled separately
            if k == "params":
                continue

            setattr(self.schema, k, v)

        self.params = module_params_to_schema[
            f"{properties['module']}:{properties['crossChainCommand']}"
        ].from_dict(properties["params"])
        self.schema.params= self.params.bytes

    @classmethod
    def validate_schema(cls, properties: dict) -> None:
        assert "module" in properties, "Missing 'module' parameter."
        assert (
            f"{properties['module']}:{properties['crossChainCommand']}" in module_params_to_schema
        ), "Invalid 'module/crossChainCommand' combination."
        assert "crossChainCommand" in properties, "Missing 'crossChainCommand' parameter."
        assert (
            len(properties["sendingChainID"]) == CHAIN_ID_LENGTH
        ), "Invalid 'sendingChainID' length."
        assert (
            len(properties["receivingChainID"]) == CHAIN_ID_LENGTH
        ), "Invalid 'receivingChainID' length."
        assert "nonce" in properties, "Missing 'nonce' parameter."
        assert properties["nonce"] >= 0, "Invalid 'nonce'."
        assert "fee" in properties, "Missing 'fee' parameter."
        assert properties["fee"] >= 0, "Invalid 'fee'."
        assert "params" in properties, "Missing 'params' parameter."
        assert "status" in properties, "Missing 'status' parameter."

    @classmethod
    def from_dict(cls, properties: dict) -> CCM:
        cls.validate_schema(properties)
        return CCM(properties)

    @property
    def module(self) -> bytes:
        return self.schema.module

    @property
    def crossChainCommand(self) -> bytes:
        return self.schema.crossChainCommand

    @property
    def receivingChainID(self) -> bytes:
        return self.schema.receivingChainID
    
    @property
    def sendingChainID(self) -> bytes:
        return self.schema.sendingChainID

    @property
    def nonce(self) -> int:
        return self.schema.nonce

    @property
    def fee(self) -> int:
        return self.schema.fee
    
    @property
    def status(self) -> int:
        return self.schema.status

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

    def __str__(self) -> str:
        return json.dumps(self.to_dict)

class Params(object):
    def __init__(self, schema: GeneratedProtocolMessageType, properties: dict[str, Any]) -> None:
        self.schema = schema
        for k, v in properties.items():
            setattr(self.schema, k, v)

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


class RegistrationParams(Params):
    def __init__(self, properties: dict[str, Any]) -> None:
        super().__init__(codec.ccm.Registration(), properties)
    
    @classmethod
    def validate_schema(cls, properties: dict) -> None:
        assert "name" in properties, "Missing 'name' parameter."
        assert 1 <= len(properties["name"]) <= 32, "Invalid 'name'."
        assert "chainID" in properties, "Missing 'chainID' parameter."
        assert len(properties["chainID"]) == CHAIN_ID_LENGTH, "Invalid 'chainID'."
        assert "messageFeeTokenID" in properties, "Missing 'messageFeeTokenID' parameter."
        assert len(properties["messageFeeTokenID"]) == TOKEN_ID_LENGTH, "Invalid 'messageFeeTokenID'."

module_params_to_schema = {"interoperability:registration": RegistrationParams}