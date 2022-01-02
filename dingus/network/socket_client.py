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
            block = api.fetch_block(event.data["id"])
            if "data" in block:
                self.emit_event("response_block", block["data"][0], ["api_response"])
        elif event.name == "request_account":
            account = api.fetch_account_from_public_key(event.data["public_key"])
            if "data" in account:
                self.emit_event("response_account", account["data"][0], ["api_response"])
            else:
                self.emit_event("response_account", {}, ["api_response"])

    def handle_new_block(self, response: dict) -> None:
        new_block_received = response["data"][0]
        self.emit_event("new_block", new_block_received, ["service_subscription"])
