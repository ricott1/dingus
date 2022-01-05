import logging
import asyncio

from dingus.types.event import Event

class ComponentMixin(object):
    def __init__(self, *args, priority=0, **kwargs) -> None:
        self.events = []
        self.priority = priority
        super().__init__(*args, **kwargs)
    
    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_running_loop() 

    async def start(self) -> None:
        raise NotImplementedError
    
    async def stop(self) -> None:
        raise NotImplementedError
    
    async def handle_event(self, event: dict) -> None:
        pass

    def handle_exception(self, exception: Exception) -> None:
        pass

    async def on_update(self, deltatime: float) -> None:
        pass
    
    def emit_event(self, name: str, data: dict, tags: list = []) -> None:
        event = Event(name, data, tags)
        logging.info(f"Emitting event: {event.name} - {event.data}")
        self.events.append(event)

    def clear_events(self) -> None:
        self.events = []
    
    def get_events_by_name(self, name:str) -> list:
        return [event for event in self.events if event.name == name]
    
    def get_events_by_tag(self, tag:str) -> list:
        return [event for event in self.events if tag in event.tags]