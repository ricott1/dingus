from dingus.constants import EVENT_TAGS

class Event(object):
    def __init__(self, name: str, data: dict, tags: list = []) -> None:
        for t in tags:
            assert t in EVENT_TAGS, "Invalid event tag."
        self.name = name
        self.data = data
        self.tags = tags
        