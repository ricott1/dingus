import socketio
import logging
import time
import dingus.network.api as api
import dingus.component as component

class DingusClient(component.ComponentMixin, socketio.AsyncClient):

    async def start(self) -> None:
        logging.info("Firing up Dingus socket client")
        self.on("update.block", self.handle_new_block, '/blockchain')
        io_server = "wss://service.lisk.com"
        logging.info(f"Connecting to {io_server}...")
        i = 0
        while not self.connected:
            i += 1
            logging.info(f"Trying to connect: #{i}")
            try:
                await self.connect(io_server, namespaces=['/blockchain'])
                logging.info("Socket client connected!!")
            except socketio.exceptions.ConnectionError as err:
                logging.error(f"Connection error: {err}")
    
    def stop(self) -> None:
        if self.connected:
            logging.info("Disconnecting Dingus socket client")
            self.disconnect()

    async def handle_event(self, event: dict) -> None:
        if event.name == "request_block":
            # input(event)
            new_block = api.fetch_block(event.data["id"])
            if "data" in new_block:
                self.emit_event("requested_block", new_block["data"][0], ["api_response"])
            
    def handle_new_block(self, response: dict) -> None:
        new_block_received = response["data"][0]
        self.emit_event("new_block", new_block_received, ["service_subscription"])
        # self.logger.info("Emitted new_block_received")
