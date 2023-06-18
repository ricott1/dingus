from .json_schemas import transferParams, crossChainTransferParamsSchema
from .transfer_pb2 import Transfer
from .crosschaintransfer_pb2 import CrossChainTransfer

proto = {
    "transfer": Transfer,
    "transferCrossChain": CrossChainTransfer
}

json = {
    "transfer": transferParams,
    "transferCrossChain": crossChainTransferParamsSchema
}