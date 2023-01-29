from google.protobuf.reflection import GeneratedProtocolMessageType
from dataclasses import dataclass

class ReadContext(object):
    pass

class WriteContext(object):
    pass

@dataclass
class Command(object):
    module: str
    name: str
    params: dict

    def verify(self, readContext: ReadContext) -> None:
        return
    
    def execute(self, readContext: WriteContext) -> None:
        return