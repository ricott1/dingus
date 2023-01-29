from .json_schemas import sidechainRegistrationParams, mainchainRegistrationParams, mainchainRegistrationMessage
from .mainchainregistrationmessage_pb2 import MainchainRegistrationMessage
from .sidechainregistrationparams_pb2 import SidechainRegistrationParams
from .mainchainregistrationparams_pb2 import MainchainRegistrationParams

proto = {
    "registerSidechain": SidechainRegistrationParams,
    "registerMainchain": MainchainRegistrationParams,
    "mainchainRegistrationMessage": MainchainRegistrationMessage
}

json = {
    "registerSidechain": sidechainRegistrationParams,
    "registerMainchain": mainchainRegistrationParams,
    "mainchainRegistrationMessage": mainchainRegistrationMessage
}



