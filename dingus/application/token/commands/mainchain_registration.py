from typing import Any
from dingus.types.command import Command

class TokenTransferCommand(Command):
    def __init__(self, params: dict[str, Any]) -> None:
        super().__init__("token", "transfer", params)