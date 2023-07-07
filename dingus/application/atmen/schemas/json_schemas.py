from dingus.constants import Length

openSwapParamsSchema = {
	"type": 'object',
	"required": ['swapID', 'tokenID', 'value', 'recipientAddress', 'timelock', 'tip'],
	"properties": {
		"swapID": {
			"dataType": 'bytes',
            "minLength": Length.HASH,
            "maxLength": Length.HASH,
			"fieldNumber": 1,
		},
		"tokenID": {
			"dataType": 'bytes',
            "minLength": Length.TOKEN_ID,
            "maxLength": Length.TOKEN_ID,
			"fieldNumber": 2,
		},
		"value": {
			"dataType": 'uint64',
			"fieldNumber": 3,
		},
		"recipientAddress": {
			"dataType": 'bytes',
            "minLength": Length.ADDRESS,
            "maxLength": Length.ADDRESS,
			"fieldNumber": 4,
		},
		"timelock": {
			"dataType": 'uint32',
			"fieldNumber": 5,
		},
        "tip": {
            "dataType": 'uint64',
            "fieldNumber": 6,
        },
	},
}

closeSwapParamsSchema = {
	"type": 'object',
	"required": ['swapID', 'secret'],
	"properties": {
		"swapID": {
			"dataType": 'bytes',
            "minLength": Length.HASH,
            "maxLength": Length.HASH,
			"fieldNumber": 1,
		},
		"secret": {
			"dataType": 'bytes',
            "minLength": Length.HASH,
            "maxLength": Length.HASH,
			"fieldNumber": 2,
		},
	},
}
redeemSwapParamsSchema = {
	"type": 'object',
	"required": ['swapID'],
	"properties": {
		"swapID": {
			"dataType": 'bytes',
            "minLength": Length.HASH,
            "maxLength": Length.HASH,
			"fieldNumber": 1,
		},
	},
}

if __name__ == "__main__":
    from dingus.codec.utils import json_schema_to_protobuf, compile_schema
    json_schemas = {
        "openSwap": openSwapParamsSchema,
        "closeSwap": closeSwapParamsSchema,
        "redeemSwap": redeemSwapParamsSchema,
    }
    for name, js in json_schemas.items():
        proto_schema = json_schema_to_protobuf(js, name)
        print(proto_schema)
        compile_schema(proto_schema, name)