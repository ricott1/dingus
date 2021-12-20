import schemas
import utils

import transaction

class BlockHeader(object):
    VERSION = 0

    def __init__(self, ) -> None:
        raise NotImplementedError

class Block(object):
    VERSION = 0

    def __init__(self, header : BlockHeader, payload:list[transaction.Transaction], fee:int, asset_schema: GeneratedProtocolMessageType, asset_params: dict, strict:bool) -> None:
        raise NotImplementedError
