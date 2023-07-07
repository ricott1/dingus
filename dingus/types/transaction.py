from __future__ import annotations
import logging
from typing import Any

import jsonschema

import dingus.codec as codec
from dingus.codec.utils import parse_from_bytes
import dingus.crypto as crypto
import dingus.network.api as api
from dingus.constants import Length, SignatureTags
from dingus.codec.json_format import MessageToDict, ParseDict #to decode to hex
from nacl.signing import SigningKey

import os
import json



class Transaction(object):
    def __init__(self, properties: dict) -> None:
        self.json_schema = transactionSchema
        jsonschema.validate(properties, self.json_schema)
        self.proto_schema = codec.transaction.Transaction()
        
        self.module = properties["module"]
        self.command = properties["command"]
        self.nonce = int(properties["nonce"])
        self.fee = int(properties["fee"])
        if isinstance(properties["senderPublicKey"], str):
            self.senderPublicKey = bytes.fromhex(properties["senderPublicKey"])
        elif isinstance(properties["senderPublicKey"], bytes):
            self.senderPublicKey = properties["senderPublicKey"]

        if type(properties["params"]) == bytes:
            self.params = Params.from_bytes(properties["module"], properties["command"], properties["params"])
        else:
            self.params = Params(properties['module'], properties['command'], properties["params"])
        self.signatures = []
        for sig in properties["signatures"]:
            if isinstance(sig, str):
                self.signatures.append(bytes.fromhex(sig))
            elif isinstance(sig, bytes):
                self.signatures.append(sig)
        
        properties["params"] = self.params.bytes
        # Temporarily remove signatures to get signing bytes
        properties["signatures"] = []
        self.proto_schema = ParseDict(properties, self.proto_schema)
        self.unsigned_bytes = self.proto_schema.SerializeToString()
        self.proto_schema.signatures.extend(self.signatures)

    @classmethod
    def from_dict(cls, properties: dict) -> Transaction:
        if "signatures" not in properties:
            properties["signatures"] = []
        return Transaction(properties)
    
    @classmethod
    def from_bytes(cls, tx_bytes: bytes) -> Transaction:
        properties = MessageToDict(parse_from_bytes(codec.transaction.Transaction, tx_bytes))
        
        if "signatures" not in properties:
            properties["signatures"] = []
        if type(properties["params"]) == str:
            properties["params"] = bytes.fromhex(properties["params"])
        properties["params"] = Params.from_bytes(properties["module"], properties["command"], properties["params"])
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
    
    def signing_bytes(self, chainID: bytes) -> bytes:
        return crypto.hash(SignatureTags.TRANSACTION + chainID + self.unsigned_bytes)

    def sign(self, sk: SigningKey, chainID: bytes = b"") -> Transaction:
        if not chainID:
            if "CHAIN_ID" not in os.environ:
                logging.warning("Cannot sign transaction, chain ID not set.")
                return
            chainID = bytes.fromhex(os.environ["CHAIN_ID"])

        signature = sk.sign(self.signing_bytes(chainID)).signature
        self.proto_schema.signatures.extend([signature])
        self.signatures.append(signature)
        return self

    def send(self, endpoint: str = "") -> dict:
        assert self.is_signed, "Cannot send unsigned transaction."
        return api.send_transaction(self.bytes.hex(), endpoint=endpoint)

    def __str__(self) -> str:
        d = self.to_dict
        d["params"] = self.params.to_dict
        return json.dumps(d, indent=4)


class Params(object):
    def __init__(self, module: str, command: str, properties: dict[str, Any] | bytes | str) -> None:
        if isinstance(properties, str):
            properties = bytes.fromhex(properties)
        self.proto_schema = params_proto_schemas[module][command]()
        if isinstance(properties, bytes):
            properties = MessageToDict(parse_from_bytes(params_proto_schemas[module][command], properties))
        self.json_schema = params_json_schemas[module][command]
        # for k, v in properties.items():
        #     print(k, type(v))
        jsonschema.validate(properties, self.json_schema)
        
        self.proto_schema = ParseDict(properties, self.proto_schema)
        for k, v in properties.items():
            setattr(self, k, v)

    @property
    def bytes(self) -> bytes:
        return self.proto_schema.SerializeToString()
    
    @classmethod
    def from_bytes(cls, module: str, command: str, params_bytes: bytes) -> Params:
        return Params(module, command, MessageToDict(parse_from_bytes(params_proto_schemas[module][command], params_bytes)))
    
    @property
    def to_dict(self) -> dict:
        return MessageToDict(self.proto_schema)
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict, indent=4)

from dingus.application.interoperability.schemas import json as interop_json
from dingus.application.interoperability.schemas import proto as interop_proto
from dingus.application.token.schemas import json as token_json
from dingus.application.token.schemas import proto as token_proto
from dingus.application.legacy.schemas import json as legacy_json
from dingus.application.legacy.schemas import proto as legacy_proto
from dingus.application.pos.schemas import json as pos_json
from dingus.application.pos.schemas import proto as pos_proto
from dingus.application.atmen.schemas import json as atmen_json
from dingus.application.atmen.schemas import proto as atmen_proto


params_json_schemas = {
    "token": token_json,
    "interoperability": interop_json,
    "legacy": legacy_json,
    "pos": pos_json,
    "atmen": atmen_json
}
params_proto_schemas = {
    "token": token_proto,
    "interoperability": interop_proto,
    "legacy": legacy_proto,
    "pos": pos_proto,
    "atmen": atmen_proto
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