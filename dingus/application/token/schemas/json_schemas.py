from dingus.constants import Length

transferParams = {
    "type": "object",
    "required": [
        "tokenID",
        "amount",
        "recipientAddress",
        "data"
    ],
    "properties": {
        "tokenID": {
            "dataType": "bytes",
            "minLength": Length.TOKEN_ID,
            "maxLength": Length.TOKEN_ID,
            "fieldNumber": 1
        },
        "amount": {
            "dataType": "uint64",
            "fieldNumber": 2
        },
        "recipientAddress": {
            "dataType": "bytes",
            "minLength": Length.ADDRESS,
            "maxLength": Length.ADDRESS,
            "fieldNumber": 3
        },
        "data": {
            "dataType": "string",
            "maxLength": Length.DATA_MAX,
            "fieldNumber": 4
        }
    }
}

crossChainTransferParamsSchema = {
    "type": "object",
    "required": [
        "tokenID",
        "amount",
        "receivingChainID",
        "recipientAddress",
        "data",
        "messageFee",
        "messageFeeTokenID"
    ],
    "properties": {
        "tokenID": {
            "dataType": "bytes",
            "length": Length.TOKEN_ID,
            "fieldNumber": 1
        },
        "amount": {
            "dataType": "uint64",
            "fieldNumber": 2
        },
        "receivingChainID": {
            "dataType": "bytes",
            "length": Length.CHAIN_ID,
            "fieldNumber": 3
        },
        "recipientAddress": {
            "dataType": "bytes",
            "length": Length.ADDRESS,
            "fieldNumber": 4
        },
        "data": {
            "dataType": "string",
            "maxLength": Length.DATA_MAX,
            "fieldNumber": 5
        },
        "messageFee": {
            "dataType": "uint64",
            "fieldNumber": 6
        },
        "messageFeeTokenID": {
            "dataType": "bytes",
            "length": Length.TOKEN_ID,
            "fieldNumber": 7
        }
    }
}

if __name__ == "__main__":
    from dingus.codec.utils import json_schema_to_protobuf, compile_schema
    json_schemas = {
        "transfer": transferParams,
        "crossChainTransfer": crossChainTransferParamsSchema
    }
    for name, js in json_schemas.items():
        proto_schema = json_schema_to_protobuf(js, name)
        compile_schema(proto_schema, name)