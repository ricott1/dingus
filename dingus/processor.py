import asyncio
import sys
import dingus.urwid_tui.tui as tui
import dingus.network.socket_client as socket


class Processor(object):
    def __init__(self):
        self.event_loop = asyncio.new_event_loop()
        self.components = [
            socket.DingusClient(),
            tui.TUI()
        ]
        print("Starting with components", self.components)
        asyncio.run(self.start())
       
    async def stop(self, *args):
        for comp in self.components:
            comp.stop()
        tasks = asyncio.all_tasks(self.event_loop)
        if tasks:
            print("Terminating tasks", tasks)
            await asyncio.wait(tasks, timeout=2)

    async def start(self) -> None:
        await asyncio.gather(*[asyncio.create_task(comp.start()) for comp in self.components])
        deltatime = 0.02
        exit_flag = False
        try:
            while not exit_flag:
                await asyncio.wait([comp.on_update(deltatime) for comp in self.components])
                events = []
                for comp in self.components:
                    events += comp.events
                    comp.clear_events()
                for event in events: 
                    if event.name == "quit_input":
                        exit_flag = True
                        break
                    for comp in self.components:
                        await comp.handle_event(event)
                    # [asyncio.create_task(comp.handle_event(event)) for comp in self.components]
                    await asyncio.wait([comp.handle_event(event) for comp in self.components])
                await asyncio.sleep(deltatime)
        finally:
            await self.stop()
            
            



