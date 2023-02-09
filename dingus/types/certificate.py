from __future__ import annotations
import logging
import os
import json

import jsonschema

from dingus.types.block import BlockHeader
import dingus.network.api as api
import dingus.crypto as crypto
from dingus.constants import Length, SignatureTags
import dingus.codec as codec
from dingus.codec.json_format import MessageToDict, ParseDict #to decode to hex

class Certificate(object):
    def __init__(self, properties: dict) -> None:
        self.unsigned_json_schema = unsignedCertificateSchema
        self.json_schema = certificateSchema
        self.unsigned_proto_schema = codec.certificate.Certificate()
        self.proto_schema = codec.certificate.Certificate()
        unsigned_properties = {k: v for k, v in properties.items() if k != "signature"}
        if "signature" in properties:
            jsonschema.validate(properties, self.json_schema)   
        else:
            jsonschema.validate(properties, self.unsigned_json_schema)
            properties["signature"] = b""   
            
        self.unsigned_proto_schema = ParseDict(unsigned_properties, self.unsigned_proto_schema)
        self.proto_schema = ParseDict(properties, self.proto_schema)
        for k, v in properties.items():
            setattr(self, k, v)
        
        self.unsigned_bytes = self.unsigned_proto_schema.SerializeToString()

    def from_block_header(block_header: BlockHeader, endpoint: str = "") -> Certificate:
        height = block_header.aggregateCommit["height"]
        target_header = api.get_block_by_height(height, endpoint)["result"]["header"]
        return Certificate(
            {
                "blockID": target_header["id"],
                "height": target_header["height"],
                "timestamp": target_header["timestamp"],
                "stateRoot": target_header["stateRoot"],
                "validatorsHash": target_header["validatorsHash"],
                "aggregationBits": block_header.aggregateCommit["aggregationBits"],
                "signature": block_header.aggregateCommit["certificateSignature"]
            }
        )

    @classmethod
    def from_dict(cls, properties: dict) -> Certificate:
        return Certificate(properties)

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
        return len(self.proto_schema.signature) > 0
    
    @property
    def signing_bytes(self) -> bytes:
        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot get signing bytes, chain ID not set.")
            return bytes()

        net_id = bytes.fromhex(os.environ["CHAIN_ID"])
        return crypto.hash(SignatureTags.CERTIFICATE + net_id + self.unsigned_bytes)
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict, indent=4)
    
unsignedCertificateSchema = {
    "type": "object",
    "required": [
        "blockID",
        "height",
        "timestamp",
        "stateRoot",
        "validatorsHash",
        "aggregationBits"
    ],
    "properties": {
        "blockID": {
            "dataType": "bytes",
            "fieldNumber": 1
        },
        "height": {
            "dataType": "uint32",
            "fieldNumber": 2
        },
        "timestamp": {
            "dataType": "uint32",
            "fieldNumber": 3
        },
        "stateRoot": {
            "dataType": "bytes",
            "fieldNumber": 4
        },
        "validatorsHash": {
            "dataType": "bytes",
            "fieldNumber": 5
        },
        "aggregationBits": {
            "dataType": "bytes",
            "fieldNumber": 6
        }
    }
}

certificateSchema = unsignedCertificateSchema.copy()
certificateSchema["required"].append("signature")
certificateSchema["properties"]["signature"] = {
    "dataType": "bytes",
    "fieldNumber": 7
}