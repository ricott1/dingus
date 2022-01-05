import socketio
import asyncio
import logging
import os
import time
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
        if "data" in status:
            self.emit_event("network_status_update", status, ["api_response"])
            os.environ["DINGUS_NETWORK_ID"] = status["data"]["networkIdentifier"]
            os.environ["DINGUS_BLOCK_TIME"] = str(status["data"]["blockTime"])
            self.last_update_time = status["meta"]["lastUpdate"]

        fees = api.network_fees()
        if "data" in fees:
            os.environ["DINGUS_MIN_FEE_PER_BYTE"] = str(fees["data"]["minFeePerByte"])
        prices= api.market_prices()
        if "data" in prices:
            self.emit_event("market_prices_update", prices["data"], ["api_response"])

        
    def stop(self) -> None:
        if self.connected:
            logging.info("Disconnecting Dingus socket client")
            try:
                asyncio.wait(self.disconnect())
            except Exception as e:
                print(e)

    async def handle_event(self, event: dict) -> None:
        if event.name == "request_block":
            block = api.fetch_block(event.data["key"], event.data["value"])
            if "data" in block:
                self.emit_event("response_block", block["data"][0], ["api_response"])
        elif event.name == "request_account":
            account = api.fetch_account(event.data["key"], event.data["value"])
            if "response_name" in event.data:
                name = event.data["response_name"]
            else:
                name = "response_account"
            
            if "data" in account:
                self.emit_event(name, account["data"][0], ["api_response"])
            else:
                default = {
                    "address": "",
                    "balance": "0",
                    "username": "",
                    "publicKey": "",
                    "isDelegate": "false",
                    "isMultisignature": "false"

                }
                default[event.data["key"]] = event.data["value"]
                self.emit_event(name, {"summary": default}, ["api_response"])

    def handle_new_block(self, response: dict) -> None:
        status = api.network_status()
        self.emit_event("network_status_update", status, ["service_subscription"])
        self.last_update_time = status["meta"]["lastUpdate"]

    def log_event(self, name:str, response: dict) -> None:
        if "data" in response:
            logging.info(f"Subscribe API event {name}: {response['data']}")
    
    async def on_update(self, deltatime: float) -> None:
        if time.time() - self.last_update_time > int(os.environ["DINGUS_BLOCK_TIME"]):
            status = api.network_status()
            self.emit_event("network_status_update", status, ["api_response"])
            prices= api.market_prices()
            if "data" in prices:
                self.emit_event("market_prices_update", prices["data"], ["api_response"])

            self.last_update_time = status["meta"]["lastUpdate"]
