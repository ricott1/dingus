from .json_schemas import openSwapParamsSchema, closeSwapParamsSchema, redeemSwapParamsSchema
from .openswap_pb2 import OpenSwap
from .closeswap_pb2 import CloseSwap
from .redeemswap_pb2 import RedeemSwap

proto = {
    "openSwap": OpenSwap,
    "closeSwap": CloseSwap,
    "redeemSwap": RedeemSwap
}

json = {
    "openSwap": openSwapParamsSchema,
    "closeSwap": closeSwapParamsSchema,
    "redeemSwap": redeemSwapParamsSchema
}