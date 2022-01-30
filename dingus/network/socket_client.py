import socketio
import logging
import os
import time
import dingus.network.api as api
import dingus.component as component
from dingus.network.constants import SOCKET_ENDPOINTS


class DingusClient(component.ComponentMixin):
    async def start(self) -> None:
        logging.info("Firing up Dingus socket client")

        status = api.network_status()
        if "data" in status:
            self.emit_event("network_status_update", status, ["api_response"])
            os.environ["NETWORK_ID"] = status["data"]["networkIdentifier"]
            os.environ["BLOCK_TIME"] = str(status["data"]["blockTime"])
            self.last_update_time = status["meta"]["lastUpdate"]

        fees = api.network_fees()
        if "data" in fees:
            os.environ["MIN_FEE_PER_BYTE"] = str(fees["data"]["minFeePerByte"])
        prices = api.market_prices()
        if "data" in prices:
            self.emit_event("market_prices_update", prices["data"], ["api_response"])

    async def handle_event(self, event: dict) -> None:
        if event.name == "request_block":
            block = api.fetch_block(event.data["key"], event.data["value"])
            if "response_name" in event.data:
                name: str = event.data["response_name"]
            else:
                name = "response_block"

            if "data" in block:
                self.emit_event(name, block["data"][0], ["api_response"])

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
                    "isMultisignature": "false",
                }
                default[event.data["key"]] = event.data["value"]
                self.emit_event(name, {"summary": default}, ["api_response"])

    def log_event(self, name: str, response: dict) -> None:
        if "data" in response:
            logging.info(f"Subscribe API event {name}: {response['data']}")

    async def on_update(self, deltatime: float) -> None:
        if time.time() - self.last_update_time > int(os.environ["BLOCK_TIME"]):
            status = api.network_status()
            if "data" in status:
                self.emit_event("network_status_update", status, ["api_response"])
            if "meta" in status:
                self.last_update_time = status["meta"]["lastUpdate"]
                if status["meta"]["lastBlockHeight"] // 20 == 0:
                    prices = api.market_prices()
                    if "data" in prices:
                        self.emit_event(
                            "market_prices_update", prices["data"], ["api_response"]
                        )
