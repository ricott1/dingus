import urwid
import json
import os
import traceback

import dingus.component as component
import dingus.transaction as transaction
import dingus.urwid_tui.frames as frames
import dingus.urwid_tui.prompts as prompts
from dingus.urwid_tui.utils import PALETTE, WIDTH, HEIGHT, create_button, terminal_size, attr_button, rgb_list_to_text
from dingus.types.event import Event
import dingus.utils as utils
from dingus.constants import LSK
import dingus.types.keys as keys


class TUI(component.ComponentMixin, urwid.Pile):
    def __init__(self) -> None:
        self.warning_frame = frames.WarningFrame()
        _title = urwid.BoxAdapter(frames.TitleFrame(["Dingus"]), height=12)
        self.base_header = CurrentTipHeader(self)
        _header = urwid.LineBox(urwid.BoxAdapter(self.base_header, height=4), title = "Dingus")
        
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
        print("Traceback: ", traceback.format_exc())
        if exc:
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
        else:
            if hasattr(self.active_body, "handle_input"):
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
        _body = urwid.SimpleFocusListWalker([urwid.Text("\n Fetching network status...")])
        super().__init__(_body, **kwargs)
    
    def update_status(self, data: dict) -> None:
        if "data" not in data:
            return

        text = f"Current tip\nheight {data['data']['height']}"
        tip_btn = attr_button(
            text, 
            borders=False,
            on_press=lambda btn: self.parent.emit_event(
                "request_block", 
                {"key": "height", "value": data['data']['height']}, 
                ["user_input"]
            )
        )
       
        text = f"Last finalized\nheight {data['data']['finalizedHeight']}"
        finalized_btn = attr_button(
            text, 
            borders=False,
            on_press=lambda btn: self.parent.emit_event(
                "request_block", 
                {"key": "height", "value": data['data']['finalizedHeight']}, 
                ["user_input"]
            )
        )
        
        self.body[:] = [
            urwid.Columns([
                    urwid.LineBox(finalized_btn), 
                    urwid.LineBox(tip_btn) 
            ])
        ]
    
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
    
    def update_block_data(self, data: dict) -> None:
        columns = []
        for k, v in data.items():
            btn = create_button(f"{v}")
            if k == "previousBlockId":
                urwid.connect_signal(btn, 'click', lambda btn, id=v: self.parent.emit_event("request_block", {"key": "id", "value": id}, ["user_input"]))
            elif k == "generatorPublicKey":
                address = keys.PublicKey(bytes.fromhex(v)).to_address().to_lsk32()
                data = {"key": "address", "value": address, "response_name": "response_account_explorer"}
                urwid.connect_signal(btn, 'click', lambda btn, id=v: self.parent.emit_event("request_account", data, ["user_input"]))
            elif k == "generatorUsername":
                data = {"key": "username", "value": v, "response_name": "response_account_explorer"}
                urwid.connect_signal(btn, 'click', lambda btn, id=v: self.parent.emit_event("request_account", data, ["user_input"]))
            elif k == "generatorAddress":
                data = {"key": "address", "value": v, "response_name": "response_account_explorer"}
                urwid.connect_signal(btn, 'click', lambda btn, id=v: self.parent.emit_event("request_account", data, ["user_input"]))
            btn = urwid.AttrMap(btn, None, focus_map="line")
            col = urwid.Columns([urwid.Text(f"\n  {k}:"), btn]) 
            columns.append(col)
        
        self.body[:] = columns
    
    def update_account_data(self, data: dict) -> None:
        if "summary" not in data:
            return
        columns = []
        for k, v in data["summary"].items():
            btn = create_button(f"{v}")
            btn = urwid.AttrMap(btn, None, focus_map="line")
            col = urwid.Columns([urwid.Text(f"\n  {k}:"), btn]) 
            columns.append(col)
        
        self.body[:] = columns
    
    async def handle_event(self, event: Event) -> None:
        if event.name == "response_block":
            self.update_block_data(event.data)
        elif event.name == "response_account_explorer":
            self.update_account_data(event.data)


class AccountInfo(frames.UiPile):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        self.accounts = {}
        new_act_btn = create_button("(N)ew", borders=False)
        urwid.connect_signal(new_act_btn, 'click', self.prompt_password)
        new_act_btn = urwid.AttrMap(new_act_btn, None, focus_map="line")
        self.select_act_btn = create_button(f"(S)elect ({len(self.accounts.keys())})", borders=False)
        urwid.connect_signal(self.select_act_btn, 'click', self.select_account)
        select_act_btn = urwid.AttrMap(self.select_act_btn, None, focus_map="line")
        self.btns = urwid.Columns([urwid.LineBox(select_act_btn), urwid.LineBox(new_act_btn)])
        
        _header = urwid.LineBox(urwid.Text(""))
        _widgets = [("pack", _header), ("pack", self.btns), urwid.ListBox(urwid.SimpleFocusListWalker([]))]
        super().__init__(_widgets, **kwargs)
        self.current_account = None
        
    
    def start(self) -> None:
        self.update_account_data()
        self.update_body()
    
    def handle_input(self, _input: str, pressed_since: float = 0) -> None:
        if _input in ("s", "S"):
            self.select_account()
        elif _input in ("n", "N"):
            self.prompt_password()
        elif _input in ("c", "C"):
            if self.current_account:
                utils.copy_to_clipboard(self.current_account)
        
    def update_account_data(self) -> None:
        accounts = os.listdir(os.environ["DINGUS_ACCOUNTS_PATH"])
        for filename in accounts:
            try:
                address = filename.split(".")[0]
                if address in self.accounts:
                    continue
                with open(f"{os.environ['DINGUS_ACCOUNTS_PATH']}/{filename}", "r") as f:
                    data = json.loads(f.read())
                public_key = keys.PublicKey(bytes.fromhex(data["public_key"]))
            except Exception as e:
                print(e)
                continue

            self.accounts[address] = {
                "balance": 0,
                "public_key": public_key,
                "nonce": 0
            }
            self.parent.emit_event("request_account", {"key": "address", "value": address, "response_name": "response_account_info"}, ["user_input"])
           
    def update_body(self) -> None:
        self.select_act_btn.set_label(f"(S)elect ({len(self.accounts.keys())})")
        # self.select_act_btn.disabled = bool(len(self.accounts) == 0)
        header_data = urwid.Text("No account data, create a new one first.", align= "center")
        body_data = [urwid.Text("")]
        if self.accounts and not self.current_account:
            self.current_account = list(self.accounts.keys())[0]

        if self.current_account:
            try:
                public_key = self.accounts[self.current_account]["public_key"]
                avatar = rgb_list_to_text(public_key.to_address().to_avatar())
                btn = attr_button(["\n"] + avatar + ["\n(C)opy"], borders=False, on_press=lambda btn : utils.copy_to_clipboard(self.current_account))
                balance = float(self.accounts[self.current_account]["balance"]) / LSK
                header_data = urwid.Columns([(16, btn), urwid.Text(f"\n\n{self.current_account}\n\n{balance} LSK", align="center")])
                
                send_btn = attr_button(["Send LSK"], borders=False, on_press=self.prompt_send_lsk)
                body_data = [urwid.LineBox(send_btn)]
                self.parent.emit_event("request_account", {"key": "address", "value": self.current_account, "response_name": "response_account_info"}, ["user_input"])
            except Exception as e:
                input(e)
                header_data = urwid.Text("Invalid account file.", align= "center")
                body_data = [urwid.Text("")]
       
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(body_data))
        self.contents[0] = (urwid.LineBox(header_data), ("pack", None))
        self.contents[1] = (self.btns, ("pack", None))
        self.contents[2] = (_body, ("weight", 1))

    def prompt_send_lsk(self, btn = None) -> None:
        bottom_w = self.contents[2][0]
        top_w = prompts.SendPrompt(self.send_lsk, self.update_body)
        _body = urwid.Overlay(top_w, bottom_w, "center", 60, ("relative", 0.5), 18)
        self.contents[0] = (urwid.WidgetDisable(self.contents[0][0]), ("pack", None))
        self.contents[1] = (urwid.WidgetDisable(self.contents[1][0]), ("pack", None))
        self.contents[2] = (_body, ("weight", 1))
        self.focus_position = 2
    
    def send_lsk(self, params: dict) -> None:
        if not utils.validate_lisk32_address(params["recipientAddress"]):
            print("Invalid lsk address")
            self.update_body()
            return

        tx_params = {
            "senderPublicKey": self.accounts[self.current_account]["public_key"].encode(),
            "nonce": self.accounts[self.current_account]["nonce"],
            "fee": params["fee"],
            "asset": {
                "amount": params["amount"],
                "recipientAddress": utils.get_address_from_lisk32_address(params["recipientAddress"]),
                "data": params["data"]
            }   
        }
        try:
            trs = transaction.BalanceTransfer.fromDict(tx_params)
            filename = self.current_account + ".json"
            private_key = keys.PrivateKey.from_json(filename, params["password"])
            trs.sign(private_key)
            trs.send()
        except Exception as e:
            print(e)
        finally:
            self.update_body()

    def prompt_password(self, btn = None) -> None:
        bottom_w = urwid.WidgetDisable(self.contents[2][0])
        top_w = prompts.PasswordPrompt(self.new_account, self.update_body)
        _body = urwid.Overlay(top_w, bottom_w, "center", 36, ("relative", 0.5), 10)
        self.contents[0] = (urwid.WidgetDisable(self.contents[0][0]), ("pack", None))
        self.contents[1] = (urwid.WidgetDisable(self.contents[1][0]), ("pack", None))
        self.contents[2] = (_body, ("weight", 1))
        self.focus_position = 2

    def new_account(self, password: str) -> None:
        sk = utils.random_private_key()
        sk.to_json(password)
        self.current_account = sk.to_public_key().to_address().to_lsk32()
        self.update_account_data()
        self.update_body()
    
    def select_account(self, btn = None) -> None:
        def select(btn, acc):
            self.current_account = acc
            self.update_body()

        if len(self.accounts) == 0:
            return
        body_data = []
        for address in self.accounts:
            public_key = self.accounts[address]["public_key"]
            avatar = rgb_list_to_text(public_key.to_address().to_avatar())
            btn = attr_button(["\n"] + avatar + ["\nselect"], borders=False, on_press=lambda btn, acc=address : select(btn, acc))
            body_data.append(urwid.Columns([(16, btn), urwid.Text(f"\n{address}", align="center")]))
            self.parent.emit_event("request_account", {"key": "address", "value": address, "response_name": "response_account_info"}, ["user_input"])
        
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(body_data))
        self.contents[2] = (_body, ("weight", 1))

    async def handle_event(self, event: Event) -> None:
        if event.name == "network_status_update":
           self.parent.emit_event("request_account", {"key": "address", "value": self.current_account, "response_name": "response_account_info"}, ["user_input"])
        elif event.name == "response_account_info" and "summary" in event.data:
            acc = event.data["summary"]["address"]
            if event.data["summary"]["publicKey"]:
                self.accounts[acc]["public_key"] = keys.PublicKey(bytes.fromhex(event.data["summary"]["publicKey"]))
            if "token" in event.data:
                self.accounts[acc]["balance"] = int(event.data["token"]["balance"])
            if "sequence" in event.data:
                self.accounts[acc]["nonce"] = int(event.data["sequence"]["nonce"])

               

