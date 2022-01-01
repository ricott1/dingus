import asyncio
import sys
import signal
import logging
import dingus.urwid_tui.tui as tui
import dingus.network.socket_client as socket



class Processor(object):
    def __init__(self, logger):
        self.logger = logger

        self.event_loop = asyncio.new_event_loop()

        self.components = [
            socket.DingusClient(logger),
            tui.TUI(logger)
        ]
        asyncio.run(self.start())
       
    def stop(self, *args):
        tasks = asyncio.all_tasks(self.event_loop)
        for task in tasks:
            task.cancel()
        for comp in self.components:
            comp.stop()

    async def start(self) -> None:
        await asyncio.gather(*[asyncio.create_task(comp.start()) for comp in self.components])
        deltatime = 0.05
        try:
            while True:
                tasks = []
                events = []
                for comp in self.components:
                    events += comp.events
                    comp.events = []
                for event in events: 
                    if event.name == "quit_input":
                        raise RuntimeError
                    for comp in self.components:
                        tasks.append(asyncio.create_task(comp.handle_event(event)))

                [asyncio.create_task(comp.on_update(deltatime)) for comp in self.components]
                # await asyncio.gather(*tasks)
                # await asyncio.gather(*[asyncio.create_task(comp.on_update(deltatime)) for comp in self.components])
                
                await asyncio.sleep(deltatime)
        except (KeyboardInterrupt, RuntimeError) as e:
            print("keyboard itnerrupted", e)
        finally:
            self.stop()
            



