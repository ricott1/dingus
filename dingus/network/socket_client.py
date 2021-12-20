import socketio
import logging
import time
import dingus.network.api as api

class DingusClient(socketio.AsyncClient):
    def __init__(self, master, logger=False) -> None:
        self.master = master
        super().__init__(logger=logger)
        self.on("update.block", self.handle_new_block, '/blockchain')
        self.events = []

    async def start(self) -> None:
        io_server = "wss://service.lisk.com"
        logging.info(f"Connecting to {io_server}...")
        i = 0
        while not self.connected:
            i += 1
            logging.info(f"Trying to connect: #{i}")
            try:
                await self.connect(io_server, namespaces=['/blockchain'])
            except socketio.exceptions.ConnectionError as err:
                logging.error(f"Connection error: {err}")
        
        logging.info("Socket client connected!!")

    def handle_new_block(self, response: dict) -> None:
        new_block_received = response["data"][0]
        self.events.append({"name": "new_block_received", "data" : new_block_received})
        new_block = api.fetch_block(new_block_received["id"])["data"][0]
        self.events.append({"name": "new_block", "data" : new_block})
