from .json_schemas import registerValidatorTransactionParams, stakeTransactionParams
from .registervalidator_pb2 import RegisterValidator
from .stake_pb2 import Stake

proto = {
    "registerValidator": RegisterValidator,
    "stake": Stake
}

json = {
    "registerValidator": registerValidatorTransactionParams,
    "stake": stakeTransactionParams
}



