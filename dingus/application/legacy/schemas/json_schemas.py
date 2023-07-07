from dingus.constants import Length, MAX_NUM_VALIDATORS, NUMBER_ACTIVE_VALIDATORS_MAINCHAIN

registerKeysParams = {
    "type": "object",
    "required": ["blsKey", "proofOfPossession", "generatorKey"],
    "properties": {
        "blsKey": {
            "dataType": "bytes",
            "length": Length.BLS_PUBLIC_KEY,
            "fieldNumber": 1
        },
        "proofOfPossession": {
            "dataType": "bytes",
            "length": Length.PROOF_OF_POSSESSION,
            "fieldNumber": 2
        },
        "generatorKey": {
            "dataType": "bytes",
            "length": Length.EDSA_PUBLIC_KEY,
            "fieldNumber": 3
        }
    }
}

unlockTestParams = {
    "type": "object",
    "required": [],
    "properties": {}
}

reclaimParams = {
    "type": "object",
    "required": ["amount"],
    "properties": {
        "amount": {
            "dataType": "uint64",
            "fieldNumber": 1
        }
    }
}


if __name__ == "__main__":
    from dingus.codec.utils import json_schema_to_protobuf, compile_schema
    json_schemas = {
        "registerKeys": registerKeysParams,
        "reclaimLSK": reclaimParams,
        "unlockTest": unlockTestParams

    }
    for name, js in json_schemas.items():
        proto_schema = json_schema_to_protobuf(js, name)
        compile_schema(proto_schema, name)