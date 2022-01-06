import logging
import urwid
import os
import traceback

import dingus.component as component
import dingus.transaction as transaction
import dingus.urwid_tui.frames as frames
import dingus.urwid_tui.prompts as prompts
from dingus.urwid_tui.utils import PALETTE, WIDTH, HEIGHT, create_button, terminal_size, attr_button, rgb_list_to_text
from dingus.types.event import Event
import dingus.utils as utils
from dingus.constants import LSK, BALANCE_TRANSFER_MAX_DATA_LENGTH
import dingus.types.keys as keys


class TUI(component.ComponentMixin, urwid.Pile):
    def __init__(self) -> None:
        self.warning_frame = frames.WarningFrame()
        _title = urwid.BoxAdapter(frames.TitleFrame(["Dingus"]), height=12)
        self.base_header = CurrentTipHeader(self)
        _header = urwid.LineBox(
            urwid.BoxAdapter(
                urwid.WidgetDisable(self.base_header), 
                height=4
            ), 
            title = "Dingus"
        )
        
        self.bodies = {
            "account" : AccountInfo(self),
            "explorer" : Explorer(self)
        }

        self.base_footer = MenuFooter(self)
        _footer = urwid.BoxAdapter(self.base_footer, height=3)
        super().__init__([("pack", _header), self.bodies["explorer"], ("pack", _footer)])

    @property
    def active_body(self) -> frames.UiFrame | frames.UiPile:
        return self.contents[1][0]

    @active_body.setter
    def active_body(self, _body: frames.UiFrame | frames.UiPile) -> None:
        self.contents[1] = (_body, ("weight", 1))
        if hasattr(self.active_body, "start"):
            self.active_body.start()
    
    def update_active_body(self, name: str) -> None:
        self.active_body = self.bodies[name]

    async def start(self):
        print("Starting urwid loop")
        self.loop = urwid.MainLoop(self, palette=PALETTE, event_loop=urwid.AsyncioEventLoop(loop=self.event_loop))
        self.loop.unhandled_input = self.handle_input
        self.loop.start()
        self.event_loop.set_exception_handler(self._exception_handler)
        for name in self.bodies:
            if hasattr(self.bodies[name], "start"):
                self.bodies[name].start()

    def _exception_handler(self, loop, context):
        self.stop()
        exc = context.get('exception')
        if exc:
            print("Traceback: ", traceback.format_exc())
            print(type(exc), exc, exc.__traceback__)
            if not isinstance(exc, urwid.ExitMainLoop):
                # Store the exc_info so we can re-raise after the loop stops
                urwid.compat.reraise(type(exc), exc, exc.__traceback__)
        else:
            loop.default_exception_handler(context)
        
    def stop(self):
        try:
            self.loop.stop()
        except AttributeError:
            pass

    async def handle_event(self, event: dict) -> None:
        for name in self.bodies:
            if hasattr(self.bodies[name], "handle_event"):
                await self.bodies[name].handle_event(event)
        if hasattr(self.base_header, "handle_event"):
            await self.base_header.handle_event(event)

    def handle_input(self, _input: str, pressed_since: float = 0) -> None:
        if _input in ("q", "Q", "esc"):
            self.emit_event("quit_input", {}, ["user_input"])
        elif _input in ("e", "E"):
            self.update_active_body("explorer")
        elif _input in ("a", "A"):
            self.update_active_body("account")
        elif hasattr(self.active_body, "handle_input"):
            self.active_body.handle_input(_input, pressed_since)

    async def on_update(self, _deltatime: float) -> None:
        cols, rows = terminal_size()
        if cols < WIDTH or rows < HEIGHT:
            if self.active_body is not self.warning_frame:
                self.suspended_body = self.active_body
                self.active_body = self.warning_frame
        else:
            if self.active_body is self.warning_frame:
                self.active_body = self.suspended_body
    

class CurrentTipHeader(urwid.ListBox):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        _body = urwid.SimpleFocusListWalker([urwid.Text("\n Fetching network status...", align = "center")])
        super().__init__(_body, **kwargs)
        self.initialized = False
    
    def update_status(self, data: dict) -> None:
        if "data" not in data:
            return

        text = f"Current tip\nheight {data['data']['height']}"
        event_data_tip = {"key": "height", "value": data['data']['height']}
        tip_btn = attr_button(
            text, 
            borders=False,
            on_press=lambda btn: self.request_and_switch_to_explorer("request_block", event_data_tip)
        )
       
        text = f"Last finalized\nheight {data['data']['finalizedHeight']}"
        event_data_fin = {"key": "height", "value": data['data']['finalizedHeight']}
        finalized_btn = attr_button(
            text, 
            borders=False,
            on_press=lambda btn: self.request_and_switch_to_explorer("request_block", event_data_fin)
        )
        try:
            focus_position = int(self.body[0].focus_position)
        except:
            focus_position = 0
        self.body[:] = [
            urwid.Columns([
                urwid.LineBox(finalized_btn), 
                urwid.LineBox(tip_btn) 
            ])
        ]
        self.body[0].focus_position = focus_position

        if not self.initialized:
            _header = urwid.LineBox(urwid.BoxAdapter(self, height=4), title = "Dingus")
            self.parent.contents[0] = (_header, ("pack", None))
            self.initialized = True
    
    def request_and_switch_to_explorer(self, event_name: str, event_data: dict) -> None:
        self.parent.update_active_body("explorer")
        self.parent.emit_event(
            event_name, 
            event_data, 
            ["user_input"]
        )
    
    async def handle_event(self, event: Event) -> None:
        if event.name == "network_status_update":
           self.update_status(event.data)


class MenuFooter(frames.UiFrame):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
         
        acc_btn = attr_button("(A)ccount", borders=False, on_press=lambda btn: self.parent.update_active_body("account"))
        exp_btn = attr_button("(E)xplorer", borders=False, on_press=lambda btn: self.parent.update_active_body("explorer"))
        quit_btn = attr_button("(Q)uit", borders=False, on_press=lambda btn: self.parent.emit_event("quit_input", {}, ["user_input"]))        
        _menu = [
            urwid.LineBox(acc_btn),
            urwid.LineBox(exp_btn),
            urwid.LineBox(quit_btn)
        ] 

        _body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Columns(_menu)]))
        super().__init__(_body, **kwargs)


class Explorer(urwid.ListBox):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        _body = urwid.SimpleFocusListWalker([urwid.Text("")])
        super().__init__(_body, **kwargs)
    
    def display_block(self, data: dict) -> None:
        rows = [urwid.Text("\nBlock\n", align="center")]
        for k, v in data.items():
            btn = create_button(f"{v}", borders = False)
            if k == "previousBlockId":
                urwid.connect_signal(
                    btn, 
                    'click', 
                    lambda btn, id=v: self.parent.emit_event(
                        "request_block", 
                        {"key": "blockId", "value": id}, 
                        ["user_input"]
                    )
                )

            elif k == "maxHeightPreviouslyForged" or k == "maxHeightPrevoted":
                urwid.connect_signal(
                    btn, 
                    'click', 
                    lambda btn, height=v: self.parent.emit_event(
                        "request_block", 
                        {"key": "height", "value": height}, 
                        ["user_input"]
                    )
                )
            
            elif k == "generatorPublicKey":
                address = keys.PublicKey(bytes.fromhex(v)).to_address().to_lsk32()
                data = {"key": "address", "value": address, "response_name": "response_account_explorer"}
                urwid.connect_signal(
                    btn, 
                    'click', 
                    lambda btn, id=v: self.parent.emit_event(
                        "request_account", 
                        data, 
                        ["user_input"]
                    )
                )

            elif k == "generatorUsername":
                data = {"key": "username", "value": v, "response_name": "response_account_explorer"}
                urwid.connect_signal(
                    btn, 
                    'click', 
                    lambda btn, id=v: self.parent.emit_event(
                        "request_account", 
                        data, 
                        ["user_input"]
                    )
                )
            elif k == "generatorAddress":
                data = {"key": "address", "value": v, "response_name": "response_account_explorer"}
                urwid.connect_signal(
                    btn, 
                    'click', 
                    lambda btn, id=v: self.parent.emit_event(
                        "request_account", 
                        data, 
                        ["user_input"]
                    )
                )

            btn = urwid.AttrMap(btn, None, focus_map="line")
            col = urwid.Columns([urwid.Text(f" {k}:    ", align="right"), btn]) 
            rows.append(col)
        
        self.body[:] = rows
    
    def display_account(self, data: dict) -> None:
        rows = [urwid.Text("\nAccount\n", align="center")]
        for k, v in data.items():
            rows.append(urwid.Text(f"{k}\n", align="center"))
            for k1, v1 in v.items():
                btn = create_button(f"{v1}", borders = False)
                btn = urwid.AttrMap(btn, None, focus_map="line")
                col = urwid.Columns([urwid.Text(f" {k1}:    "), btn]) 
                rows.append(col)
        
        
        self.body[:] = rows
    
    async def handle_event(self, event: Event) -> None:
       
        if event.name == "response_block":
            self.display_block(event.data)
        elif event.name == "response_account_explorer":
            self.display_account(event.data)


class AccountInfo(frames.UiPile):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        self.accounts = {}

        new_act_btn = attr_button(
            "(N)ew", 
            borders=False, 
            on_press = self.prompt_new_account
        )

        select_act_btn = attr_button(
            f"(S)elect", 
            borders=False,
            on_press = self.select_account
        )
        self.selecting_account = False

        import_act_btn = attr_button(
            f"(I)mport", 
            borders=False,
            on_press = self.prompt_import_account
        )

        bookmark_act_btn = attr_button(
            f"(B)ookmark", 
            borders=False,
            on_press = self.prompt_bookmark_account
        )

        _btns = urwid.Columns([
            urwid.LineBox(select_act_btn), 
            urwid.LineBox(new_act_btn),
            urwid.LineBox(import_act_btn),
            urwid.LineBox(bookmark_act_btn)
            ])
        
        _header = urwid.LineBox(urwid.Text(""))

        self.send_btn = attr_button(
            ["Send LSK"], 
            borders=False, 
            on_press=self.prompt_send_lsk
        )

        self.remove_bookmark_btn = attr_button(
            ["Remove Bookmark"], 
            borders=False, 
            on_press=self.remove_bookmark
        )

        self.base_body = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        
        _widgets = [("pack", _header), ("pack", _btns), self.base_body]
        super().__init__(_widgets, **kwargs)
        self._current_address = None
        self.update_header()
        self.price_feeds = {"LSK_EUR" : 0}

    @property
    def current_address(self) -> str:
        return self._current_address
    @current_address.setter
    def current_address(self, value: str) -> None:
        self._current_address = value
        self.update_header()
    
    @property
    def current_account(self) -> dict | None:
        if not self.current_address:
            return None
        if self.current_address not in self.accounts:
            return None
        return self.accounts[self.current_address]
        
    def start(self) -> None:
        self.update_account_data()
    
    def handle_input(self, _input: str, pressed_since: float = 0) -> None:
        if _input in ("s", "S"):
            self.select_account()
        elif _input in ("n", "N"):
            self.prompt_new_account()
        elif _input in ("i", "I"):
            self.prompt_import_account()
        elif _input in ("b", "B"):
            self.prompt_bookmark_account()
        elif _input in ("c", "C"):
            if self.current_address:
                utils.copy_to_clipboard(self.current_address)

    def update_account_data(self) -> None:
        def select_btn(addr):
            self.reset_base_body()
            self.current_address = addr
            
        accounts = os.listdir(f"{os.environ['DINGUS_BASE_PATH']}/accounts")
        for filename in accounts:
            data = utils.load_account(filename)

            if not data or "address" not in data or data["address"] in self.accounts:
                continue

            address = data["address"]
            avatar = data["avatar"] = rgb_list_to_text(utils.lisk32_to_avatar(address))
            name = data["name"]
                
            btn = attr_button(
                ["\n"] + avatar + ["\nselect"], 
                borders = False, 
                on_press = lambda btn, acc=address : select_btn(acc)
            )
            selection_entry = urwid.Columns([
                (16, btn), 
                urwid.Text(f"\n{name}\n{address}", align="center")
            ])
            data["selection"] = selection_entry

            self.accounts[address] = data
            
            event_data = {"key": "address", "value": address, "response_name": "response_account_info"}
            self.parent.emit_event("request_account", event_data, ["user_input"])
        
        if self.accounts:
            if not self.current_address:
                self.current_address = list(self.accounts.keys())[0]
        else:
            self.current_address = None
    
    def reset_base_body(self):
        self.contents[2] = (self.base_body, ("weight", 1))
        self.focus_position = 1
    
    def request_and_switch_to_explorer(self, event_name: str, event_data: dict) -> None:
        self.parent.update_active_body("explorer")
        self.parent.emit_event(
            event_name, 
            event_data, 
            ["user_input"]
        )
        
    def update_header(self) -> None:
        if not self.current_account:
            header_data = urwid.Text("\n\n\nNo account data, create a new one first.\n\n\n", align= "center")
        else:
            avatar = self.current_account["avatar"]
            name = self.current_account["name"]

            btn = attr_button(
                ["\n"] + avatar + ["\n(C)opy"], 
                borders = False, 
                on_press = lambda btn : utils.copy_to_clipboard(self.current_address)
            )

            event_data = {
                "key": "address", 
                "value": self.current_address, 
                "response_name": "response_account_explorer"
            }

            top = urwid.LineBox(
                attr_button(
                    f"{name}\n{self.current_address}", 
                    borders = False,
                    on_press = lambda btn : self.request_and_switch_to_explorer("request_account", event_data)
                )
            ) 

            balance = float(self.current_account["balance"]) / LSK
            lsk_to_eur = balance * self.price_feeds["LSK_EUR"]

            if self.current_account["bookmark"]:
                    bottom = urwid.Columns([
                    urwid.LineBox(self.remove_bookmark_btn),
                    urwid.Text(f"\n{balance} LSK = {lsk_to_eur:.2f} EUR", align="center")
                ])
            else:
                bottom = urwid.Columns([
                    urwid.LineBox(self.send_btn),
                    urwid.Text(f"\n{balance} LSK = {lsk_to_eur:.2f} EUR", align="center")
                ])

            header_data = urwid.Columns([
                (16, btn),
                urwid.Pile([top, bottom])
            ])
            
        self.contents[0] = (urwid.LineBox(header_data), ("pack", None))

    def prompt_send_lsk(self, btn = None) -> None:
        if not self.current_address:
            return
        bottom_w = urwid.WidgetDisable(self)
        top_w = prompts.SendPrompt(self.send_lsk, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 60, ("relative", 15), 20)
        self.parent.active_body = _overlay
    
    def send_lsk(self, params: dict) -> None:
        if not self.current_address:
            return
        if self.current_account["bookmark"]:
            self.prompt_text("Cannot sign transaction using bookmark account.")
            return
            
        if not utils.validate_lisk32_address(params["recipientAddress"]):
            self.prompt_text("Invalid lsk address")
            return
        try:
            fee = float(params["fee"])
        except ValueError:
            self.prompt_text("Invalid fee")
            return
        
        try:
            amount = float(params["amount"])
        except ValueError:
            self.prompt_text("Invalid amount")
            return
        
        if fee <= 0:
            self.prompt_text("Invalid fee")
            return
        
        if amount <= 0:
            self.prompt_text("Invalid amount")
            return

        if len(params["data"]) > BALANCE_TRANSFER_MAX_DATA_LENGTH:
            self.prompt_text(f"Data exceeds maximum length. {len(params['data'])} > {BALANCE_TRANSFER_MAX_DATA_LENGTH}.")
            return

        tx_params = {
            "senderPublicKey": self.current_account["public_key"],
            "nonce": self.current_account["nonce"],
            "fee": int(fee * LSK),
            "asset": {
                "amount": int(amount * LSK),
                "recipientAddress": utils.get_address_from_lisk32_address(params["recipientAddress"]),
                "data": params["data"]
            }   
        }

        trs = transaction.BalanceTransfer.fromDict(tx_params)
        logging.info(f"Sending transaction {trs}")

        try:
            filename = self.current_address + ".json"
            private_key = keys.PrivateKey.from_json(filename, params["password"])
            trs.sign(private_key)
            result = trs.send()
        except Exception as e:
            self.prompt_text(f"Error: {e}")
            return

        if "error" in result:
            self.prompt_text(f"Transaction {trs.id.hex()} errored!\n{result['message']}", title="Error")
        else:
            # Increase nonce here in case user send multiple transaction
            # within one block. Real value will be overwritten on next block.
            self.current_account["nonce"] += 1
            self.prompt_text(f"Transaction {trs.id.hex()} sent!", title="Success")

    def destroy_prompt(self) -> None:
        self.parent.active_body = self
        self.reset_base_body()
    
    def prompt_text(self, text: str = "There was an error", title: str = "Error") -> None:
        bottom_w = urwid.WidgetDisable(self)
        top_w = prompts.TextPrompt(text, title, self.destroy_prompt)
        _width = 48
        _height = 16 + len(text)//_width
        _overlay = urwid.Overlay(top_w, bottom_w, "center", _width, ("relative", 15), _height)
        self.parent.active_body = _overlay

    def prompt_new_account(self, btn = None) -> None:
        bottom_w = urwid.WidgetDisable(self)
        top_w = prompts.NewAccountPrompt(self.create_new_account, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 48, ("relative", 15), 13)
        self.parent.active_body = _overlay

    def create_new_account(self, name: str, password: str) -> None:
        sk = utils.random_private_key()
        data = sk.encrypt(password)
        public_key = sk.to_public_key().hexbytes()
        address = sk.to_public_key().to_address().to_lsk32()

        data["name"] = name
        data["address"] = address
        data["public_key"] = public_key
        filename = f"{address}.json"
        utils.save_account(filename, data)

        self.update_account_data()
        self.current_address = address
        self.destroy_prompt()
    
    def prompt_import_account(self, btn = None) -> None:
        bottom_w = urwid.WidgetDisable(self)
        top_w = prompts.ImportPrompt(self.import_account, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 60, ("relative", 15), 19)
        self.parent.active_body = _overlay
    
    def import_account(self, name: str, password: str, passphrase: str) -> None:
        sk = keys.PrivateKey.from_passphrase(passphrase)
        address = sk.to_public_key().to_address().to_lsk32()
        if address in self.accounts:
            self.prompt_text("Address already imported.")
            return

        data = sk.encrypt(password)
        public_key = sk.to_public_key().hexbytes()
        data["name"] = name
        data["address"] = address
        data["public_key"] = public_key
        filename = f"{address}.json"
        utils.save_account(filename, data)
        
        self.update_account_data()
        self.current_address = address
        self.destroy_prompt()
    
    def prompt_bookmark_account(self, btn = None) -> None:
        bottom_w = urwid.WidgetDisable(self)
        top_w = prompts.BookmarkPrompt(self.bookmark_account, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 48, ("relative", 15), 13)
        self.parent.active_body = _overlay
    
    def bookmark_account(self, name: str, address: str) -> None:
        if not utils.validate_lisk32_address(address):
            self.prompt_text("Invalid lsk address")
            return

        if address in self.accounts:
            self.prompt_text("Address already followed.")
            return
        
        data = {}
        data["name"] = name
        data["address"] = address
        filename = f"bookmark.{address}.json"
        utils.save_account(filename, data)
        self.update_account_data()
        self.current_address = address
        self.destroy_prompt()
    
    def remove_bookmark(self, btn = None) -> None:
        filename = f"bookmark.{self.current_address}.json"
        utils.delete_account(filename)
        del self.accounts[self.current_address]
        self.current_address = None
        self.reset_base_body()
        self.update_account_data()

    def select_account(self, btn = None) -> None:
        if self.selecting_account:
            self.selecting_account = False
            self.reset_base_body()
        else:
            self.selecting_account = True
            select_account_btns = [self.accounts[address]["selection"] for address in self.accounts]
            _body = urwid.ListBox(urwid.SimpleFocusListWalker(select_account_btns))
            self.contents[2] = (_body, ("weight", 1))
            self.focus_position = 2
            

    async def handle_event(self, event: Event) -> None:
        if event.name == "network_status_update":
            data = {"key": "address", "value": self.current_address, "response_name": "response_account_info"}
            self.parent.emit_event("request_account", data, ["user_input"])
        elif event.name == "market_prices_update":
            if event.data:
                self.update_header()
            for feed in event.data:
                self.price_feeds[feed["code"]] = float(feed["rate"])
        elif event.name == "response_account_info" \
            and "summary" in event.data \
            and "address" in event.data["summary"]:
            address = event.data["summary"]["address"]
            account_changed = False
            if "publicKey" in event.data and event.data["summary"]["publicKey"]:
                public_key = event.data["summary"]["publicKey"]
                if self.accounts[address]["public_key"] != public_key:
                    self.accounts[address]["public_key"] = public_key
                    account_changed = True
            if "token" in event.data:
                balance = int(event.data["token"]["balance"])
                if self.accounts[address]["balance"] != balance:
                    self.accounts[address]["balance"] = balance
                    account_changed = True
            if "sequence" in event.data:
                nonce = int(event.data["sequence"]["nonce"])
                if self.accounts[address]["nonce"] != nonce:
                    self.accounts[address]["nonce"] = nonce
                    account_changed = True
                self.accounts[address]["nonce"] = int(event.data["sequence"]["nonce"])
            
            if account_changed:
                filename = f"{address}.json"
                account_data = {k: v for k, v in self.accounts[address].items() if k not in ("avatar", "selection")}
                utils.save_account(filename, account_data)
