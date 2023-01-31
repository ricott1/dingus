from __future__ import annotations

import dingus.codec as codec
import dingus.crypto as crypto
import logging
import json
from dingus.codec.utils import normalize_bytes
from dingus.types.transaction import Transaction
from dingus.constants import Length, SignatureTags
import dingus.network.api as api
import jsonschema
import os
from dingus.constants import Length
from dingus.codec.json_format import MessageToDict #to decode to hex
from dingus.types.keys import SigningKey
from google.protobuf.json_format import  ParseDict


class Block(object):
    def __init__(self, properties: dict) -> None:
        self.json_schema = blockSchema
        jsonschema.validate(properties, self.json_schema)
        self.proto_schema = codec.block.Block()
        
        for k, v in properties.items():
            # header and signature are not set directly
            if k == "header":
                continue
            setattr(self, k, v)
        
        self.header = BlockHeader(properties['header'])
        properties["header"] = self.header.bytes
        self.proto_schema = ParseDict(normalize_bytes(properties), self.proto_schema)

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


class BlockHeader(object):
    def __init__(self, properties: dict) -> None:
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
            
        self.unsigned_proto_schema = ParseDict(normalize_bytes(unsigned_properties), self.unsigned_proto_schema)
        self.proto_schema = ParseDict(normalize_bytes(properties), self.proto_schema)
        for k, v in properties.items():
            setattr(self, k, v)
        
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
    
    @property
    def signing_bytes(self) -> bytes:
        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot get signing bytes, chain ID not set.")
            return
        net_id = os.environ["CHAIN_ID"]
        return crypto.hash(SignatureTags.BLOCK_HEADER + net_id + self.unsigned_bytes)

    def sign(self, sk: SigningKey) -> BlockHeader:
        if "CHAIN_ID" not in os.environ:
            logging.warning("Cannot sign block header, network ID not set.")
            return

        signature = sk.sign(self.signing_bytes).signature
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