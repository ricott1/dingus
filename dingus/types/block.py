from __future__ import annotations

import dingus.codec as codec
import dingus.crypto as crypto
import logging
import json
from typing import TYPE_CHECKING
from dingus.types.transaction import Transaction
from dingus.utils import get_address_from_lisk32_address
from dingus.constants import Length, SignatureTags
import dingus.network.api as api
import jsonschema
import os
from dingus.codec.json_format import MessageToDict, ParseDict #to decode to hex
from dingus.types.keys import SigningKey


class Block(object):
    def __init__(self, properties: dict) -> None:
        self.json_schema = blockSchema
        self.proto_schema = codec.block.Block()
        self.header = BlockHeader(properties['header'])
        self.assets = [Asset(asset) for asset in properties['assets']]
        self.transactions = []
        for tx in properties['transactions']:
            try:
                self.transactions.append(Transaction.from_dict(tx) )
            except:
                continue
    
        properties["header"] = self.header.bytes
        properties["assets"] = [asset.bytes for asset in self.assets]
        properties["transactions"] = [tx.bytes for tx in self.transactions]
        jsonschema.validate(properties, self.json_schema)
        self.proto_schema = ParseDict(properties, self.proto_schema)

    @classmethod
    def from_dict(cls, properties: dict) -> Block:
        return Block(properties)

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
        return self.header.is_signed

    def sign(self, sk: SigningKey) -> Block:
        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot sign block, network ID not set.")
            return

        self.header.sign(sk)
        return self

    def __str__(self) -> str:
        d = self.to_dict
        d["header"] = self.header.to_dict
        return json.dumps(d, indent=4)

class Asset(object):
    def __init__(self, properties: dict) -> None:
        self.json_schema = assetSchema
        jsonschema.validate(properties, self.json_schema)
        self.proto_schema = codec.block.Asset()
        self.proto_schema = ParseDict(properties, self.proto_schema)

    @classmethod
    def from_dict(cls, properties: dict) -> Asset:
        return Asset(properties)

    @property
    def bytes(self) -> bytes:
        return self.proto_schema.SerializeToString()

    @property
    def to_dict(self) -> dict:
        return MessageToDict(self.proto_schema)

    def __str__(self) -> str:
        return json.dumps(self.to_dict, indent=4)

class BlockHeader(object):
    def __init__(self, properties: dict) -> None:
        if properties["generatorAddress"].startswith("lsk"):
            properties["generatorAddress"] = get_address_from_lisk32_address(properties["generatorAddress"])
        if "id" in properties:
            del properties["id"]
        self.unsigned_json_schema = unsignedBlockHeaderSchema
        self.json_schema = blockHeaderSchema
        self.unsigned_proto_schema = codec.block.Header()
        self.proto_schema = codec.block.Header()
        unsigned_properties = {k: v for k, v in properties.items() if k != "signature"}
        if "signature" in properties:
            jsonschema.validate(properties, self.json_schema)   
        else:
            jsonschema.validate(properties, self.unsigned_json_schema)
            properties["signature"] = b""   
            
        self.unsigned_proto_schema = ParseDict(unsigned_properties, self.unsigned_proto_schema)
        self.proto_schema = ParseDict(properties, self.proto_schema)

        self.version = int(properties["version"])
        self.timestamp = int(properties["timestamp"])
        self.height = int(properties["height"])

        if isinstance(properties["previousBlockID"], str):
            properties["previousBlockID"] = bytes.fromhex(properties["previousBlockID"])
        self.previousBlockID = properties["previousBlockID"]
        
        if isinstance(properties["generatorAddress"], str):
            properties["generatorAddress"] = bytes.fromhex(properties["generatorAddress"])
        self.generatorAddress = properties["generatorAddress"]
        
        if isinstance(properties["transactionRoot"], str):
            properties["transactionRoot"] = bytes.fromhex(properties["transactionRoot"])
        self.transactionRoot = properties["transactionRoot"]
        
        if isinstance(properties["assetRoot"], str):
            properties["assetRoot"] = bytes.fromhex(properties["assetRoot"])
        self.assetRoot = properties["assetRoot"]
        
        if isinstance(properties["eventRoot"], str):
            properties["eventRoot"] = bytes.fromhex(properties["eventRoot"])
        self.eventRoot = properties["eventRoot"]
        
        if isinstance(properties["stateRoot"], str):
            properties["stateRoot"] = bytes.fromhex(properties["stateRoot"])
        self.stateRoot = properties["stateRoot"]
        
        self.maxHeightPrevoted = int(properties["maxHeightPrevoted"])
        self.maxHeightGenerated = int(properties["maxHeightGenerated"])
        self.impliesMaxPrevotes = bool(properties["impliesMaxPrevotes"])
        
        if isinstance(properties["validatorsHash"], str):
            properties["validatorsHash"] = bytes.fromhex(properties["validatorsHash"])
        self.validatorsHash = properties["validatorsHash"]
        
        if isinstance(properties["aggregateCommit"]["aggregationBits"], str):
            properties["aggregateCommit"]["aggregationBits"] = bytes.fromhex(properties["aggregateCommit"]["aggregationBits"])
        if isinstance(properties["aggregateCommit"]["certificateSignature"], str):
            properties["aggregateCommit"]["certificateSignature"] = bytes.fromhex(properties["aggregateCommit"]["certificateSignature"])
        properties["aggregateCommit"]["height"] = int(properties["aggregateCommit"]["height"])
        self.aggregateCommit = properties["aggregateCommit"]

        self.unsigned_bytes = self.unsigned_proto_schema.SerializeToString()

    @classmethod
    def from_dict(cls, properties: dict) -> BlockHeader:
        return BlockHeader(properties)

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

    def signing_bytes(self, chainID: bytes) -> bytes:
        return crypto.hash(SignatureTags.BLOCK_HEADER + chainID + self.unsigned_bytes)

    def sign(self, sk: SigningKey, chainID: bytes = b"") -> BlockHeader:
        if not chainID:
            if "CHAIN_ID" not in os.environ:
                logging.warning("Cannot sign block header, network ID not set.")
                return
            chainID = bytes.fromhex(os.environ["CHAIN_ID"])

        signature = sk.sign(self.signing_bytes(chainID)).signature
        self.proto_schema.signature = signature
        self.signature = signature
        return self

    def __str__(self) -> str:
        return json.dumps(self.to_dict, indent=4)



blockSchema = {
  "type": "object",
  "required": ["header", "transactions", "assets"],
  "properties": {
    "header": {
      "dataType": "bytes",
      "fieldNumber": 1
    },
    "transactions": {
      "type": "array",
      "fieldNumber": 2,
      "items": {
        "dataType": "bytes"
      }
    },
    "assets": {
      "type": "array",
      "fieldNumber": 3,
      "items": {
        "dataType": "bytes"
      }
    }
  }
}

assetSchema = {
  "type": "object",
  "required": ["module", "data"],
  "properties": {
    "module": {
      "dataType": "string",
      "minLength": Length.MODULE_NAME_MIN,
      "maxLength": Length.MODULE_NAME_MAX,
      "fieldNumber": 1
    },
    "data": {
      "dataType": "bytes",
      "fieldNumber": 2
    }
  }
}

unsignedBlockHeaderSchema = {
  "type": "object",
  "required": [
    "version",
    "timestamp",
    "height",
    "previousBlockID",
    "generatorAddress",
    "transactionRoot",
    "assetRoot",
    "eventRoot",
    "stateRoot",
    "maxHeightPrevoted",
    "maxHeightGenerated",
    "impliesMaxPrevotes",
    "validatorsHash",
    "aggregateCommit"
  ],
  "properties": {
    "version": {
      "dataType": "uint32",
      "fieldNumber": 1
    },
    "timestamp": {
      "dataType": "uint32",
      "fieldNumber": 2
    },
    "height": {
      "dataType": "uint32",
      "fieldNumber": 3
    },
    "previousBlockID": {
      "dataType": "bytes",
      "fieldNumber": 4
    },
    "generatorAddress": {
      "dataType": "bytes",
      "fieldNumber": 5
    },
    "transactionRoot": {
      "dataType": "bytes",
      "fieldNumber": 6
    },
    "assetRoot": {
      "dataType": "bytes",
      "fieldNumber": 7
    },
    "eventRoot": {
      "dataType": "bytes",
      "fieldNumber": 8
    },
    "stateRoot": {
      "dataType": "bytes",
      "fieldNumber": 9
    },
    "maxHeightPrevoted": {
      "dataType": "uint32",
      "fieldNumber": 10
    },
    "maxHeightGenerated": {
      "dataType": "uint32",
      "fieldNumber": 11
    },
    "impliesMaxPrevotes": {
      "dataType": "boolean",
      "fieldNumber": 12
    },
    "validatorsHash": {
      "dataType": "bytes",
      "fieldNumber": 13
    },
    "aggregateCommit": {
      "type": "object",
      "fieldNumber": 14,
      "required": [
        "height",
        "aggregationBits",
        "certificateSignature"
      ],
      "properties": {
        "height": {
          "dataType": "uint32",
          "fieldNumber": 1
        },
        "aggregationBits": {
          "dataType": "bytes",
          "fieldNumber": 2
        },
        "certificateSignature": {
          "dataType": "bytes",
          "fieldNumber": 3
        }
      }
    }
  }
}

blockHeaderSchema = unsignedBlockHeaderSchema.copy()
blockHeaderSchema["required"].append("signature")
blockHeaderSchema["properties"]["signature"] = {
    "dataType": "bytes",
    "fieldNumber": 15
}