from .json_schemas import reclaimParams, registerKeysParams, unlockTestParams
from .registerkeys_pb2 import RegisterKeys
from .reclaimlsk_pb2 import ReclaimLSK
from .unlocktest_pb2 import UnlockTest

proto = {
    "registerKeys": RegisterKeys,
    "reclaimLSK": ReclaimLSK,
    "unlockTest": UnlockTest
}

json = {
    "registerKeys": registerKeysParams,
    "reclaimLSK": reclaimParams,
    "unlockTest": unlockTestParams
}



