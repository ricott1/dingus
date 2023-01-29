from .json_schemas import transferParams
from .transfer_pb2 import Transfer

proto = {
    "transfer": Transfer
}

json = {
    "transfer": transferParams
}