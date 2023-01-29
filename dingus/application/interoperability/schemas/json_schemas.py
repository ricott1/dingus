from dingus.constants import Length, MAX_NUM_VALIDATORS, NUMBER_ACTIVE_VALIDATORS_MAINCHAIN

mainchainRegistrationParams = {
    "type": "object",
    "required": [
        "ownChainID",
        "ownName",
        "mainchainValidators",
        "mainchainCertificateThreshold",
        "signature",
        "aggregationBits"
    ],
    "properties": {
        "ownChainID": {
            "dataType": "bytes",
            "minLength": Length.CHAIN_ID,
            "maxLength": Length.CHAIN_ID,
            "fieldNumber": 1
        },
        "ownName": {
            "dataType": "string",
            "minLength": Length.CHAIN_NAME_MIN,
            "maxLength": Length.CHAIN_NAME_MAX,
            "fieldNumber": 2
        },
        "mainchainValidators": {
            "type": "array",
            "minItems": 1,
            "maxItems": NUMBER_ACTIVE_VALIDATORS_MAINCHAIN,
            "fieldNumber": 3,
            "items": {
                "type": "object",
                "required": ["blsKey", "bftWeight"],
                "properties": {
                    "blsKey": {
                        "dataType": "bytes",
                        "minLength": Length.BLS_PUBLIC_KEY,
                        "maxLength": Length.BLS_PUBLIC_KEY,
                        "fieldNumber": 1
                    },
                    "bftWeight": {
                        "dataType": "uint64",
                        "minimum": 1,
                        "fieldNumber": 2
                    }
                }
            }
        },
        "mainchainCertificateThreshold": {
            "dataType": "uint64",
            "fieldNumber": 4
        },
        "signature": {
            "dataType": "bytes",
            "minLength": Length.BLS_SIGNATURE,
            "maxLength": Length.BLS_SIGNATURE,
            "fieldNumber": 5
        },
        "aggregationBits": {
            "dataType": "bytes",
            "fieldNumber": 6
        }
    }
}

sidechainRegistrationParams = {
    "type": "object",
    "required": [
        "chainID",
        "name",
        "sidechainValidators",
        "sidechainCertificateThreshold"
    ],
    "properties": {
        "chainID": {
            "dataType": "bytes",
            "minLength": Length.CHAIN_ID,
            "maxLength": Length.CHAIN_ID,
            "fieldNumber": 1
        },
        "name": {
            "dataType": "string",
            "minLength": Length.CHAIN_NAME_MIN,
            "maxLength": Length.CHAIN_NAME_MAX,
            "fieldNumber": 2
        },
        "sidechainValidators": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_NUM_VALIDATORS,
            "fieldNumber": 3,
            "items": {
                "type": "object",
                "required": ["blsKey", "bftWeight"],
                "properties": {
                    "blsKey": {
                        "dataType": "bytes",
                        "minLength": Length.BLS_PUBLIC_KEY,
                        "maxLength": Length.BLS_PUBLIC_KEY,
                        "fieldNumber": 1
                    },
                    "bftWeight": {
                        "dataType": "uint64",
                        "minimum": 1,
                        "fieldNumber": 2
                    }
                }
            }
        },
        "sidechainCertificateThreshold": {
            "dataType": "uint64",
            "fieldNumber": 4
        }
    }
}

mainchainRegistrationMessage = {  
    "type": "object",
    "required": ["ownChainID", "ownName", "mainchainValidators", "mainchainCertificateThreshold"],
    "properties": {
        "ownChainID": {
            "dataType": "bytes",
            "minLength": Length.CHAIN_ID,
            "maxLength": Length.CHAIN_ID,
            "fieldNumber": 1
        },
        "ownName": {
            "dataType": "string",
            "minLength": Length.CHAIN_NAME_MIN,
            "maxLength": Length.CHAIN_NAME_MAX,
            "fieldNumber": 2
        },
        "mainchainValidators": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_NUM_VALIDATORS,
            "fieldNumber": 3,
            "items": {
                "type": "object",
                "required": ["blsKey", "bftWeight"],
                "properties": {
                    "blsKey": {
                        "dataType": "bytes",
                        "minLength": Length.BLS_PUBLIC_KEY,
                        "maxLength": Length.BLS_PUBLIC_KEY,
                        "fieldNumber": 1
                    },
                    "bftWeight": {
                        "dataType": "uint64",
                        "minimum" : 1,
                        "fieldNumber": 2
                    }
                }
            }
        },
        "mainchainCertificateThreshold": {
            "dataType": "uint64",
            "fieldNumber": 4
        }
    }
}

if __name__ == '__main__':
    import jsonschema
    jsonschema.validate(
        {
        "ownChainID": bytes.fromhex("04000123"),
        "ownName": "inverno",
        "mainchainValidators": [ 
            {"blsKey": bytes.fromhex("04"*32), "bftWeight": 1},
        ],
        "mainchainCertificateThreshold": 48
        },
        mainchainRegistrationMessage)