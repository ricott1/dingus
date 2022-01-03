import socketio
import asyncio
import logging
import os
import dingus.network.api as api
import dingus.component as component
from dingus.network.constants import SOCKET_ENDPOINTS

class DingusClient(component.ComponentMixin, socketio.AsyncClient):

    async def start(self) -> None:
        logging.info("Firing up Dingus socket client")
        self.on("update.block", self.handle_new_block, '/blockchain')
        self.on("*", self.log_event, '/blockchain')
        net = os.environ["DINGUS_NETWORK"]
        io_server = SOCKET_ENDPOINTS[net]
        logging.info(f"Connecting to {io_server}...")
        i = 0
        while not self.connected:
            i += 1
            logging.info(f"Trying to connect: #{i}")
            try:
                await self.connect(io_server, namespaces=['/blockchain'], wait=False)
                logging.info("Socket client connected!!")
            except socketio.exceptions.ConnectionError as err:
                logging.error(f"Connection error: {err}")
        
        status = api.network_status()
        self.emit_event("network_status_update", status, ["service_subscription"])
        os.environ["DINGUS_NETWORK_ID"] = status["data"]["networkIdentifier"]
        
    def stop(self) -> None:
        if self.connected:
            logging.info("Disconnecting Dingus socket client")
            try:
                asyncio.run(self.disconnect())
            except Exception as e:
                print(e)

    async def handle_event(self, event: dict) -> None:
        if event.name == "request_block":
            block = api.fetch_block(event.data["key"], event.data["value"])
            if "data" in block:
                self.emit_event("response_block", block["data"][0], ["api_response"])
        elif event.name == "request_account":
            account = api.fetch_account(event.data["key"], event.data["value"])
            name = event.data["response_name"]
            if "data" in account:
                self.emit_event(name, account["data"][0], ["api_response"])
            else:
                self.emit_event(name, {}, ["api_response"])

    def handle_new_block(self, response: dict) -> None:
        status = api.network_status()
        self.emit_event("network_status_update", status, ["service_subscription"])

    def log_event(self, name:str, response: dict) -> None:
        if "data" in response:
            logging.info(f"Subscribe API event {name}: {response['data']}")
