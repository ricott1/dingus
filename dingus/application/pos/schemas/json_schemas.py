from dingus.constants import Length, MAX_NUM_VALIDATORS, NUMBER_ACTIVE_VALIDATORS_MAINCHAIN

registerValidatorTransactionParams = {
    "type": "object",
    "required": [
        "name",
        "blsKey",
        "proofOfPossession",
        "generatorKey"
    ],
    "properties": {
        "name": {
            "dataType": "string",
            "fieldNumber": 1
        },
        "blsKey": {
            "dataType": "bytes",
            "length" : Length.BLS_PUBLIC_KEY,
            "fieldNumber": 2
        },
        "proofOfPossession": {
            "dataType": "bytes",
            "length" : Length.PROOF_OF_POSSESSION,
            "fieldNumber": 3
        },
        "generatorKey": {
            "dataType": "bytes",
            "length": Length.EDSA_PUBLIC_KEY,
            "fieldNumber": 4
        }
    }
}

stakeTransactionParams = {
    "type": "object",
    "required": ["stakes"],
    "properties": {
        "stakes": {
            "type": "array",
            "fieldNumber": 1,
            "items": {
                "type": "object",
                "required": ["validatorAddress", "amount"],
                "properties": {
                    "validatorAddress" : {
                        "dataType": "bytes",
                        "length": Length.ADDRESS,
                        "fieldNumber": 1
                    },
                    "amount": {
                        "dataType": "sint64",
                        "fieldNumber": 2
                    }
                }
            }
        }
    }
}


if __name__ == "__main__":
    from dingus.codec.utils import json_schema_to_protobuf, compile_schema
    # compile_schemas()
    
    json_schemas = {
        "registerValidator": registerValidatorTransactionParams,
        "stake": stakeTransactionParams
    }
    for name, js in json_schemas.items():
        proto_schema = json_schema_to_protobuf(js, name)
        compile_schema(proto_schema, name)