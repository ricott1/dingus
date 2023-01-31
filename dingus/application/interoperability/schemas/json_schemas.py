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

crossChainUpdateTransactionParams = {
    "type": "object",
    "required": [
        "sendingChainID",
        "certificate",
        "activeValidatorsUpdate",
        "certificateThreshold",
        "inboxUpdate"
    ],
    "properties": {
        "sendingChainID": {
            "dataType": "bytes",
            "minLength": Length.CHAIN_ID,
            "maxLength": Length.CHAIN_ID,
            "fieldNumber": 1
        },
        "certificate": {
            "dataType": "bytes",
            "fieldNumber": 2
        },
        "activeValidatorsUpdate": {
            "type": "object",
            "fieldNumber": 3,
            "required": [
                "blsKeysUpdate",
                "bftWeightsUpdate",
                "bftWeightsUpdateBitmap"
            ],
            "properties": {
                "blsKeysUpdate": {
                    "type": "array",
                    "fieldNumber": 1,
                    "items": {
                        "dataType": "bytes",
                        "minLength": Length.BLS_PUBLIC_KEY,
                        "maxLength": Length.BLS_PUBLIC_KEY
                    }
                },
                "bftWeightsUpdate": {
                    "type": "array",
                    "fieldNumber": 2,
                    "items": {
                        "dataType": "uint64",
                    }
                },
                "bftWeightsUpdateBitmap": {
                    "dataType": "bytes",
                    "fieldNumber": 3
                }
            }
        },
        "certificateThreshold": {
            "dataType": "uint64",
            "fieldNumber": 4
        },
        "inboxUpdate": {
            "type": "object",
            "fieldNumber": 5,
            "required": [
                "crossChainMessages",
                "messageWitnessHashes",
                "outboxRootWitness"
            ],
            "properties": {
                "crossChainMessages": {
                    "type": "array",
                    "fieldNumber": 1,
                    "items": {"dataType": "bytes"}
                },
                "messageWitnessHashes": {
                    "type": "array",
                    "fieldNumber": 2,
                    "items": {
                        "dataType": "bytes",
                        "minLength": Length.HASH,
                        "maxLength": Length.HASH
                    }
                },
                "outboxRootWitness": {
                    "type": "object",
                    "fieldNumber": 3,
                    "required": ["bitmap", "siblingHashes"],
                    "properties": {
                        "bitmap": {
                            "dataType": "bytes",
                            "fieldNumber": 1
                        },
                        "siblingHashes": {
                            "type": "array",
                            "fieldNumber": 2,
                            "items": {
                                "dataType": "bytes",
                                "minLength": Length.HASH,
                                "maxLength": Length.HASH
                            }
                        }
                    }
                }
            }
        }
    }
}

crossChainMessageSchema = {
    "type": "object",
    "required": [
        "module",
        "crossChainCommand",
        "nonce",
        "fee",
        "sendingChainID",
        "receivingChainID",
        "params",
        "status"
    ],
    "properties": {
        "module": {
            "dataType": "string",
            "minLength": Length.MODULE_NAME_MIN,
            "maxLength": Length.MODULE_NAME_MAX,
            "fieldNumber": 1
        },
        "crossChainCommand": {
            "dataType": "string",
            "minLength": Length.CCCOMMAND_NAME_MIN,
            "maxLength": Length.CCCOMMAND_NAME_MAX,
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
        "sendingChainID": {
            "dataType": "bytes",
            "minLength": Length.CHAIN_ID,
            "maxLength": Length.CHAIN_ID,
            "fieldNumber": 5
        },
        "receivingChainID": {
            "dataType": "bytes",
            "minLength": Length.CHAIN_ID,
            "maxLength": Length.CHAIN_ID,
            "fieldNumber": 6
        },
        "params": {
            "dataType": "bytes",
            "fieldNumber": 7
        },
        "status": {
            "dataType": "uint32",
            "fieldNumber": 8
        }
    }
}


if __name__ == "__main__":
    from dingus.codec.utils import json_schema_to_protobuf, compile_schema
    json_schemas = {
        "registerSidechain": sidechainRegistrationParams,
        "registerMainchain": mainchainRegistrationParams,
        "mainchainRegistrationMessage": mainchainRegistrationMessage,
        "crossChainUpdate": crossChainUpdateTransactionParams,
        "crossChainMessage": crossChainMessageSchema,

    }
    for name, js in json_schemas.items():
        proto_schema = json_schema_to_protobuf(js, name)
        compile_schema(proto_schema, name)