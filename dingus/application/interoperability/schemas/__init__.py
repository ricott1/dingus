from .json_schemas import sidechainRegistrationParams, mainchainRegistrationParams, mainchainRegistrationMessage, crossChainMessageSchema, crossChainUpdateTransactionParams
from .mainchainregistrationmessage_pb2 import MainchainRegistrationMessage
from .registersidechain_pb2 import RegisterSidechain
from .registermainchain_pb2 import RegisterMainchain
from .crosschainmessage_pb2 import CrossChainMessage
from .crosschainupdate_pb2 import CrossChainUpdate

proto = {
    "registerSidechain": RegisterSidechain,
    "registerMainchain": RegisterMainchain,
    "mainchainRegistrationMessage": MainchainRegistrationMessage,
    "crossChainMessage": CrossChainMessage,
    "submitSidechainCrossChainUpdate": CrossChainUpdate,
    "submitMainchainCrossChainUpdate": CrossChainUpdate,
}

json = {
    "registerSidechain": sidechainRegistrationParams,
    "registerMainchain": mainchainRegistrationParams,
    "mainchainRegistrationMessage": mainchainRegistrationMessage,
    "crossChainMessage": crossChainMessageSchema,
    "submitSidechainCrossChainUpdate": crossChainUpdateTransactionParams,
    "submitMainchainCrossChainUpdate": crossChainUpdateTransactionParams,
}



