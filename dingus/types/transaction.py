from __future__ import annotations
import logging
from typing import Any

import jsonschema

import dingus.codec as codec
from dingus.codec.utils import normalize_bytes
import dingus.crypto as crypto
import dingus.network.api as api
from dingus.constants import Length, SignatureTags
from dingus.codec.json_format import MessageToDict #to decode to hex
from google.protobuf.json_format import  ParseDict
from nacl.signing import SigningKey

import os
import json



class Transaction(object):
    def __init__(self, properties: dict) -> None:
        self.json_schema = transactionSchema
        jsonschema.validate(properties, self.json_schema)
        self.proto_schema = codec.transaction.Transaction()
        
        for k, v in properties.items():
            # params are not set directly
            if k == "params":
                continue
            setattr(self, k, v)
        
        self.params = Params(properties['module'], properties['command'], properties["params"])
        properties["params"] = self.params.bytes
        properties["signatures"] = []
        self.proto_schema = ParseDict(normalize_bytes(properties), self.proto_schema)
        # Temporarily remove signatures to get signing bytes
        self.unsigned_bytes = self.proto_schema.SerializeToString()
        self.proto_schema.signatures.extend(self.signatures)


    @classmethod
    def from_dict(cls, properties: dict) -> Transaction:
        return Transaction(properties)

    @property
    def bytes(self) -> bytes:
        return self.proto_schema.SerializeToString()

    @property
    def to_dict(self) -> dict:
        return MessageToDict(self.proto_schema)

    @property
    def id(self) -> bytes:
        return crypto.hash(self.bytes)

    @property
    def is_signed(self) -> bool:
        return len(self.proto_schema.signatures) > 0
    
    @property
    def signing_bytes(self) -> bytes:
        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot get signing bytes, chain ID not set.")
            return bytes()

        net_id = bytes.fromhex(os.environ["CHAIN_ID"])
        return crypto.hash(SignatureTags.TRANSACTION + net_id + self.unsigned_bytes)

    def sign(self, sk: SigningKey) -> Transaction:
        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot sign transaction, network ID not set.")
            return

        signature = crypto.sign(self.signing_bytes, sk)
        self.proto_schema.signatures.extend([signature])
        self.signatures.append(signature)
        return self

    def send(self) -> None:
        assert self.is_signed, "Cannot send unsigned transaction."
        return api.send_transaction(self.bytes.hex())

    def __str__(self) -> str:
        d = self.to_dict
        d["params"] = self.params.to_dict
        return json.dumps(d, indent=4)


class Params(object):
    def __init__(self, module: str, command: str, properties: dict[str, Any]) -> None:
        self.json_schema = params_json_schemas[module][command]
        jsonschema.validate(properties, self.json_schema)
        self.proto_schema = params_proto_schemas[module][command]()
        self.proto_schema = ParseDict(normalize_bytes(properties), self.proto_schema)
        for k, v in properties.items():
            setattr(self, k, v)

    @property
    def bytes(self) -> bytes:
        return self.proto_schema.SerializeToString()
    
    @property
    def to_dict(self) -> dict:
        return MessageToDict(self.proto_schema)
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict, indent=4)

from dingus.application.interoperability.schemas import json as interop_json
from dingus.application.interoperability.schemas import proto as interop_proto
from dingus.application.token.schemas import json as token_json
from dingus.application.token.schemas import proto as token_proto

params_json_schemas = {
    "token": token_json,
    "interoperability": interop_json
}
params_proto_schemas = {
    "token": token_proto,
    "interoperability": interop_proto
}

transactionSchema = {
    "type": "object",
    "required": [
        "module",
        "command",
        "nonce",
        "fee",
        "senderPublicKey",
        "params",
        "signatures"
    ],
    "properties": {
        "module": {
            "dataType": "string",
            "minLength": Length.MODULE_NAME_MIN,
            "maxLength": Length.MODULE_NAME_MAX,
            "fieldNumber": 1
        },
        "command": {
            "dataType": "string",
            "minLength": Length.COMMAND_NAME_MIN,
            "maxLength": Length.COMMAND_NAME_MAX,
            "fieldNumber": 2
        },
        "nonce": {
            "dataType": "uint64",
            "fieldNumber": 3
        },
        "fee": {
            "dataType": "uint64",
            "fieldNumber": 4
        },
        "senderPublicKey": {
            "dataType": "bytes",
            "length": Length.EDSA_PUBLIC_KEY,
            "fieldNumber": 5
        },
        "params": {
            "dataType": "bytes",
            "fieldNumber": 6
        },
        "signatures": {
            "dataType": "array",
            "items": {
                "dataType": "bytes",
                "length": Length.EDSA_SIGNATURE
            },
            "fieldNumber": 7
        }
    }
}