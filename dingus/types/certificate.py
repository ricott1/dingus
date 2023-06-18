from __future__ import annotations
import typing
import json
import os
import logging

import jsonschema
from dingus.codec.utils import parse_from_bytes

from dingus.types.block import BlockHeader
import dingus.network.api as api
import dingus.crypto as crypto
from dingus.constants import Length, SignatureTags
import dingus.codec as codec
from dingus.codec.json_format import MessageToDict, ParseDict #to decode to hex\
import blspy as bls

class Validator(typing.TypedDict):
    blsKey: bytes
    bftWeight: int

class ActiveValidatorsUpdate(typing.TypedDict):
    blsKeysUpdate: list[bytes]
    bftWeightsUpdate: list[int]
    bftWeightsUpdateBitmap: bytes

class Certificate(object):
    def __init__(self, properties: dict) -> None:
        self.unsigned_json_schema = unsignedCertificateSchema
        self.json_schema = certificateSchema
        self.unsigned_proto_schema = codec.certificate.Certificate()
        self.proto_schema = codec.certificate.Certificate()
        unsigned_properties = {k: v for k, v in properties.items() if k not in ("signature", "aggregationBits")}
        if "signature" in properties and "aggregationBits" in properties:
            jsonschema.validate(properties, self.json_schema)   
        else:
            jsonschema.validate(properties, self.unsigned_json_schema)
            properties["signature"] = b""
            properties["aggregationBits"] = b""   
            
        self.unsigned_proto_schema = ParseDict(unsigned_properties, self.unsigned_proto_schema)
        self.proto_schema = ParseDict(properties, self.proto_schema)
        for k, v in properties.items():
            setattr(self, k, v)
        
        self.unsigned_bytes = self.unsigned_proto_schema.SerializeToString()
    
    @classmethod
    def from_dict(cls, properties: dict) -> Certificate:
        return Certificate(properties)
    
    @classmethod
    def from_bytes(cls, certificate_bytes: bytes) -> Certificate:
        return parse_from_bytes(codec.certificate.Certificate, certificate_bytes)

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
        return len(self.proto_schema.signature) == Length.BLS_SIGNATURE

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
    
    def verify_signature(self, validators: list[Validator], threshold: int, chainID: bytes) -> bool:
        if not self.is_signed:
            return False
        # sort validatorList lexicographically by blsKey property
        validatorList = sorted(validators, key=lambda validator: validator["blsKey"])
        keys_list = [validator["blsKey"] for validator in validatorList]
        bft_weights = [validator["bftWeight"] for validator in validatorList]
        return crypto.verifyWeightedAggSig(keys_list, self.aggregationBits, self.signature, SignatureTags.CERTIFICATE, chainID, bft_weights, threshold, self.unsigned_bytes)
    
    def signing_bytes(self, chainID: bytes) -> bytes:
        return crypto.hash(SignatureTags.CERTIFICATE + chainID + self.unsigned_bytes)
    
    def sign(self, bls_public_keys: list[bls.G1Element], bls_private_keys: list[bls.PrivateKey], chainID: bytes = b"") -> Certificate:
        if not chainID:
            if "CHAIN_ID" not in os.environ:
                logging.warning("Cannot sign certificate, chain ID not set.")
                return
            chainID = bytes.fromhex(os.environ["CHAIN_ID"])

        keys_and_signatures = []
        for sk in bls_private_keys:
            pk = sk.get_g1()
            keys_and_signatures.append((pk, crypto.signBLS(sk, SignatureTags.CERTIFICATE, chainID, self.unsigned_bytes(chainID))))

        agg_bits, signature = crypto.createAggSig(
            bls_public_keys,
            keys_and_signatures,
        )   
        self.proto_schema.aggregationBits = agg_bits
        self.aggregationBits = agg_bits
        self.proto_schema.signature = signature
        self.signature = signature
        return self
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict, indent=4)

def get_active_validators_update(current_validators: list[Validator], new_validators: list[Validator]) -> ActiveValidatorsUpdate:
    # Get the blsKeysUpdate.
    current_BLS_keys = [v["blsKey"] for v in current_validators]
    new_BLS_keys = [v["blsKey"] for v in new_validators]
    blsKeysUpdate = sorted([blsKey for blsKey in new_BLS_keys if blsKey not in current_BLS_keys])

    validatorsUpdate: list[Validator] = []
    for validator in new_validators:
        # We add the validator to the validatorsUpdate unless an entry with the same BLS key and BFT weight already exists in currentValidators.
        # In particular:
        #  - if a current validator changes BFT weight, it gets added to the list;
        #  - new validators which were not in currentValidators are added to the list.
        if validator not in current_validators:
            validatorsUpdate.append(validator)

    for validator in current_validators:
        # We add the validator to the validatorsUpdate (with 0 BFT weight) if the BLS key is not in the newValidators.
        if validator["blsKey"] not in new_BLS_keys:
            validatorsUpdate.append({'blsKey': validator["blsKey"], 'bftWeight': 0})

    validatorsUpdate = sorted(validatorsUpdate, key=lambda v: v["blsKey"])

    # Get the bftWeightsUpdate.
    bftWeightsUpdate = [validator["bftWeight"] for validator in validatorsUpdate]

    # Get bftWeightsUpdateBitmap
    all_BLS_keys = sorted([blsKey for blsKey in set(current_BLS_keys + new_BLS_keys)])
    bitmap = 0
    bitmapSize = (len(all_BLS_keys) + 7) // 8
    for validator in validatorsUpdate:
        idx = all_BLS_keys.index(validator["blsKey"])
        bitmap |= 1 << idx

    bftWeightsUpdateBitmap = bitmap.to_bytes(bitmapSize, "big")

    return {
        "blsKeysUpdate": blsKeysUpdate,
        "bftWeightsUpdate": bftWeightsUpdate,
        "bftWeightsUpdateBitmap": bftWeightsUpdateBitmap
    }

# def getCertificateFromAggregateCommit(aggregateCommit: AggregateCommit) -> Certificate:
#     blockHeader = block header at height aggregateCommit.height
#     unsignedCertificate = computeUnsignedCertificateFromBlockHeader(blockHeader)
#     certificate = Certificate object with properties set to corresponding property of unsignedCertificate
#                   and aggregationBits, signature set to empty bytes
#     certificate.aggregationBits = aggregateCommit.aggregationBits
#     certificate.signature = aggregateCommit.certificateSignature
#     return certificate

# def checkChainOfTrust(lastValidatorsHash: bytes, blsKeyToBFTWeight: dict[bytes, uint64], lastCertificateThreshold: uint64, aggregateCommit: AggregateCommit) -> bool:
#     blockHeader = block header at height aggregateCommit.height - 1
#     # Certificate signers and certificate threshold for aggregateCommit are those authenticated by the last certificate
#     if lastValidatorsHash == blockHeader.validatorsHash:
#         return True

#     aggregateBFTWeight = 0
#     validators = validatorsHashPreimage[blockHeader.validatorsHash].validators
#     for i in range(length(validators)):
#         if bit i of aggregateCommit.aggregationsBits is 1:
#             # Aggregate commit must only be signed by BLS keys known to the other chain
#             if not validators[i].blsKey in blsKeyToBFTWeight:
#                 return False
#             aggregateBFTWeight += blsKeyToBFTWeight[validators[i].blsKey]
#     if aggregateBFTWeight >= lastCertificateThreshold:
#         return True
#     else:
#         return False
    
unsignedCertificateSchema = {
    "type": "object",
    "required": [
        "blockID",
        "height",
        "timestamp",
        "stateRoot",
        "validatorsHash"
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
        }
    }
}

certificateSchema = unsignedCertificateSchema.copy()
certificateSchema["required"].append("signature")
certificateSchema["required"].append("aggregationBits")
certificateSchema["properties"]["aggregationBits"] = {
    "dataType": "bytes",
    "fieldNumber": 6
}
certificateSchema["properties"]["signature"] = {
    "dataType": "bytes",
    "fieldNumber": 7
}