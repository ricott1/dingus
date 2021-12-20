import asyncio
import sys
import signal
import dingus.urwid_tui.tui as tui
import dingus.network.socket_client as socket

class Processor(object):
    def __init__(self, logger):
        self.event_loop = asyncio.new_event_loop()
        self.tasks = []
        
        self.logger = logger
        self.client = socket.DingusClient(logger)
        self.gui = tui.TUI(event_loop = self.event_loop)
        
        self.gui.loop.event_loop.set_signal_handler(signal.SIGINT, self.close)

        self.start()
        self.event_loop.run_forever()
        self._close()

    def close(self, sig, frame):
        self._close()

    def _close(self):
        self.logger.warn('SIGINT received')
        if self.client.connected:
            self.client.disconnect()
        self.gui.stop()
        for task in self.tasks:
            task.cancel()
        self.event_loop.stop()
        self.event_loop.close()

        sys.exit(0)

    async def updater(self):
        deltatime = 0.25
        while True:
            self.process(deltatime)
            await asyncio.sleep(deltatime)

    def process(self, deltatime: float) -> None:
        for event in list(self.client.events):
            # We could plugin a generic event processor here
            self.gui.handle_event(event)
            self.client.events.remove(event)
        
        self.gui.on_update(deltatime)

    def start(self) -> None:
        print("Firing up Dingus socket client")
        self.tasks.append(self.event_loop.create_task(self.client.start()))
        self.gui.start()
        print("Starting update thread")
        self.tasks.append(self.event_loop.create_task(self.updater()))
        

        
        



