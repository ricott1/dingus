from dingus.constants import EVENT_TAGS
from dataclasses import dataclass
from typing import Any


@dataclass
class Event(object):
    name: str
    data: dict[str, Any]
    tags: list[str]
        