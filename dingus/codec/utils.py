import os
import subprocess
from dingus.constants import Length
import base64

def normalize_bytes(properties: dict) -> None:
    '''
    Convert hex encoded bytes to base64 bytes
    '''
    for k, v in properties.items():
        if isinstance(v, bytes):
            properties[k] = base64.b64encode(v)
        elif isinstance(v, dict):
            properties[k] = normalize_bytes(v)
        elif isinstance(v, list):
            for i in range(len(v)):
                if isinstance(v[i], bytes):
                    v[i] = base64.b64encode(v[i])
                elif isinstance(v[i], dict):
                    v[i] = normalize_bytes(v[i])
            properties[k] = v
    return properties

def compile_schemas():
    for file in os.listdir("."):
        if file.endswith(".proto"):
            print(file)
            subprocess.run(["protoc", "--python_out=.", file], stdout=subprocess.PIPE)

def compile_schema(schema: str, name: str) -> bytes:
    filename = f"{name.lower()}.proto"
    with open(filename, "w") as f:
        f.write(schema)
    p = subprocess.run(["protoc", "--python_out=.", filename], stdout=subprocess.PIPE)
    return p.stdout

def json_schema_to_protobuf(schema: str | dict, name: str) -> str:
    import json
    name = name[0].upper() + name[1:]
    if isinstance(schema, str):
        schema = json.loads(schema)

    msg = f'syntax = "proto2";\n\n'
    body, req = get_proto_messages(schema, name)
    msg += body
    while req:
        key, value = req.pop()
        message_name = f"{name}_{key[0].upper()}{key[1:]}"
        body, new_req = get_proto_messages(value, message_name)
        msg += body
        req.extend(new_req)
    
    return msg

def get_proto_messages(schema: str | dict, name: str) -> tuple[str, list]:
    required_message_definitions = []
    body = ""
    for key, value in schema["properties"].items():
        body += property_to_message(key, value, name)
        if req := get_required_message_definitions(key, value):
            required_message_definitions.append(req)
    return (f'message {name} {{\n    {body}}}\n\n', required_message_definitions)

def get_required_message_definitions(key, value):
    if "type" in value and value["type"] == "object":
        return (key, value)

    if "type" in value and value["type"] == "array":
        v = value["items"]
        if "type" in v and v["type"] == "object":
            return (key, v)

def property_to_message(key, value, name):
    mappings = {
        'array': 'repeated',
        'object': 'message',
        'uint32': 'uint32',
        'uint64': 'uint64',
        'string': 'string',
        'boolean': 'bool',
        'bytes': 'bytes',
    }

    if "dataType" in value:
        return f'''\
required {mappings[value["dataType"]]} {key} = {value["fieldNumber"]};
    '''

    if "type" in value and value["type"] == "object":
        message_name = f"{name}_{key[0].upper()}{key[1:]}"
        return f'''\
required {message_name} {key} = {value["fieldNumber"]};
    '''

    if "type" in value and value["type"] == "array":
        v = value["items"]
        if "dataType" in v:
            return f'''\
repeated {v["dataType"]} {key} = {value["fieldNumber"]};
    '''

        if "type" in v and v["type"] == "object":
            message_name = f"{name}_{key[0].upper()}{key[1:]}"
            return f'''\
repeated {message_name} {key} = {value["fieldNumber"]};
    '''
        
        raise Exception("Unknown type in array.")


if __name__ == '__main__':
    msg = json_schema_to_protobuf({  
        "type": "object",
        "required": ["ownChainID", "ownName", "mainchainValidators", "mainchainCertificateThreshold"],
        "properties": {
            "ownChainID": {
                "dataType": "bytes",
                "length": Length.CHAIN_ID,
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
                "maxItems": 101,
                "fieldNumber": 3,
                "items": {
                    "type": "object",
                    "required": ["blsKey", "bftWeight"],
                    "properties": {
                        "blsKey": {
                            "dataType": "bytes",
                            "length": Length.BLS_PUBLIC_KEY,
                            "fieldNumber": 1
                        },
                        "bftWeight": {
                            "dataType": "uint64",
                            "fieldNumber": 2
                        }
                    }
                }
            },
            "mainchainCertificateThreshold": {
                "dataType": "uint64",
                "fieldNumber": 4
            },
        }
    }, "mainchainRegistrationMessage")  
    print(msg)
    compile_schema(msg, "mainchainRegistrationMessage")

