from dingus.constants import EVENT_TAGS
from dataclasses import dataclass


@dataclass
class Event(object):
    name: str
    data: dict
    tags: list[str]
        