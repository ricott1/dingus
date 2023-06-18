import logging
import os
import time
import dingus.network.api as api
import dingus.component as component


class DingusClient(component.ComponentMixin):
    async def start(self) -> None:
        logging.info("Firing up Dingus socket client")
        info = api.get_node_info()
        if "result" in info:
            self.emit_event("network_status_update", info, ["api_response"])
            os.environ["CHAIN_ID"] = info["result"]["chainID"]
            os.environ["BLOCK_TIME"] = str(info["result"]["genesis"]["blockTime"])
            self.last_update_time = time.time()
        
        fees = api.get_min_fee_per_byte()
        
        if "result" in fees:
            os.environ["MIN_FEE_PER_BYTE"] = str(fees["result"]["minFeePerByte"])
        
        price = api.kraken_market_price()
        self.emit_event("market_prices_update", price, ["api_response"])

    async def handle_events(self, events: list[dict]) -> None:
        for event in events:
            logging.info(f"Handling event {event}")
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
            status = api.get_node_info()
            self.last_update_time = time.time()
            if "result" in status:
                self.emit_event("network_status_update", status, ["api_response"])
                if status["result"]["height"] // 20 == 0:
                    price = api.kraken_market_price()
                    self.emit_event("market_prices_update", price, ["api_response"])
    
    async def stop(self) -> None:
        logging.info("Shutting down Dingus socket client")
