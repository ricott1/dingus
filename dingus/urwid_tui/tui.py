import urwid
import time
import json
import os
import logging
import traceback
from typing import Callable

import dingus.component as component
import dingus.transaction as transaction
import dingus.urwid_tui.frames as frames
from dingus.urwid_tui.utils import PALETTE, WIDTH, HEIGHT, create_button, terminal_size, attr_button, rgb_list_to_text
from dingus.types.event import Event
import dingus.utils as utils
from dingus.constants import LSK
import dingus.types.keys as keys


class TUI(component.ComponentMixin, urwid.Pile):
    def __init__(self, logger) -> None:
        self.warning_frame = frames.WarningFrame()
        _title = urwid.BoxAdapter(frames.TitleFrame(["Dingus"]), height=12)
        self.base_header = CurrentTipHeader(self)
        _header = urwid.LineBox(urwid.BoxAdapter(self.base_header, height=3), title = "Dingus")
        self.base_footer = MenuFooter(self)
        _footer = urwid.BoxAdapter(self.base_footer, height=3)
        self.bodies = {
            "account" : AccountInfo(self),
            "explorer" : BlockInfo(self)
        }
        super().__init__(logger, [("pack", _header), self.bodies["explorer"], ("pack", _footer)])

    @property
    def active_body(self) -> frames.UiFrame | frames.UiPile:
        return self.contents[1][0]

    @active_body.setter
    def active_body(self, _body: frames.UiFrame | frames.UiPile) -> None:
        self.contents[1] = (_body, ("weight", 1))
        self.active_body.start()
    
    def update_active_body(self, name: str) -> None:
        if name == "quit":
            self.emit_event("quit_input", {}, ["user_input"])
        elif name in self.bodies:
            self.active_body = self.bodies[name]

    async def start(self):
        print("Starting urwid loop")
        self.loop = urwid.MainLoop(self, palette=PALETTE, event_loop=urwid.AsyncioEventLoop(loop=self.event_loop))
        self.loop.unhandled_input = self.handle_input
        self.loop.start()
        self.event_loop.set_exception_handler(self._exception_handler)
        for name in self.bodies:
            self.bodies[name].start()

    def _exception_handler(self, loop, context):
        self.stop()
        exc = context.get('exception')
        print(traceback.format_exc())
        if exc:
            print(type(exc), exc, exc.__traceback__)
            if not isinstance(exc, urwid.ExitMainLoop):
                # Store the exc_info so we can re-raise after the loop stops
                urwid.compat.reraise(type(exc), exc, exc.__traceback__)
        else:
            loop.default_exception_handler(context)
        
    def stop(self):
        self.loop.stop()

    async def handle_event(self, event: dict) -> None:
        for name in self.bodies:
            if hasattr(self.bodies[name], "handle_event"):
                await self.bodies[name].handle_event(event)
        if hasattr(self.base_header, "handle_event"):
            await self.base_header.handle_event(event)

    def handle_input(self, _input: str, pressed_since: float = 0) -> None:
        if _input in ("q", "Q", "esc"):
            self.update_active_body("quit")
        elif _input in ("e", "E"):
            self.update_active_body("explorer")
        elif _input in ("a", "A"):
            self.update_active_body("account")
        else:
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
            if hasattr(self.base_header, "on_update"):
                await self.base_header.on_update(_deltatime)
            if hasattr(self.active_body, "on_update"):
                await self.active_body.on_update(_deltatime)
    

class CurrentTipHeader(frames.UiFrame):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        _body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("\n  Fetching current tip...")]))
        super().__init__(_body, **kwargs)
    
    def update_block_data(self, block_data: dict) -> None:
        btn = create_button(f"\nCurrent tip @ height {block_data['height']}: {block_data['id']}\n", borders=False)
        urwid.connect_signal(btn, 'click', lambda btn: self.parent.emit_event("request_block", {"id": block_data["id"]}, ["user_input"]))
        btn = urwid.AttrMap(btn, None, focus_map="line")

        _body = urwid.ListBox(urwid.SimpleFocusListWalker([btn]))
        self.contents["body"] = (_body, None)
    
    async def handle_event(self, event: Event) -> None:
        if event.name == "new_block":
           self.update_block_data(event.data)


class MenuFooter(frames.UiFrame):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        _menu = []
        opts = ("Account", "Explorer", "Quit")
        for opt in opts:
            btn = create_button(opt, borders=False)
            urwid.connect_signal(btn, 'click', lambda btn, name=opt.lower(): self.parent.update_active_body(name))
            btn = urwid.AttrMap(btn, None, focus_map="line")
            _menu.append(urwid.LineBox(btn))

        _body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Columns(_menu)]))
        super().__init__(_body, **kwargs)


class BlockInfo(frames.UiFrame):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        _body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("\n  Fetching new blocks...")]))
        super().__init__(_body, **kwargs)
    
    def update_block_data(self, block_data: dict) -> None:
        _block_data_list = [urwid.Text(f"\n  {k}: {v}") for k, v in block_data.items()]
        columns = []
        for k, v in block_data.items():
            btn = create_button(f"{v}")
            if k == "previousBlockId":
                urwid.connect_signal(btn, 'click', lambda btn, id=v: self.parent.emit_event("request_block", {"id": id}, ["user_input"]))
            btn = urwid.AttrMap(btn, None, focus_map="line")
            col = urwid.Columns([urwid.Text(f"\n  {k}:"), btn]) 
            columns.append(col)
        
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(columns))
        self.contents["body"] = (_body, None)
    
    async def handle_event(self, event: Event) -> None:
        if event.name == "response_block":
           self.update_block_data(event.data)


class AccountInfo(frames.UiPile):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        self.accounts = {}
        new_act_btn = create_button("(N)ew", borders=False)
        urwid.connect_signal(new_act_btn, 'click', self.prompt_password)
        new_act_btn = urwid.AttrMap(new_act_btn, None, focus_map="line")
        self.select_act_btn = create_button(f"(S)elect) ({len(self.accounts.keys())})", borders=False)
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
        accounts = os.listdir("dingus/accounts")
        for filename in accounts:
            try:
                address = filename.split(".")[0]
                if address in self.accounts:
                    continue
                with open(f"dingus/accounts/{filename}", "r") as f:
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
            self.parent.emit_event("request_account", {"address" : address}, ["user_input"])
           
    def update_body(self) -> None:
        self.select_act_btn.set_label(f"(S)elect) ({len(self.accounts.keys())})")
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
                self.parent.emit_event("request_account", {"address" : self.current_account}, ["user_input"])
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
        top_w = SendPrompt(self.send_lsk, self.update_body)
        _body = urwid.Overlay(top_w, bottom_w, "center", 60, ("relative", 0.5), 18)
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
            # trs.sign(private_key)
            print(trs)
            input()
        finally:
            self.update_body()

    def prompt_password(self, btn = None) -> None:
        bottom_w = urwid.WidgetDisable(self.contents[2][0])
        top_w = PasswordPrompt(self.new_account, self.update_body)
        _body = urwid.Overlay(top_w, bottom_w, "center", 36, ("relative", 0.5), 10)
        self.contents[0] = (urwid.WidgetDisable(self.contents[0][0]), ("pack", None))
        self.contents[1] = (urwid.WidgetDisable(self.contents[1][0]), ("pack", None))
        self.contents[2] = (_body, ("weight", 1))
        self.focus_position = 2

    def new_account(self, password: str) -> None:
        sk = utils.random_private_key()
        sk.to_json(password)
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
            self.parent.emit_event("request_account", {"address" : address}, ["user_input"])
        
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(body_data))
        self.contents[2] = (_body, ("weight", 1))

    async def handle_event(self, event: Event) -> None:
        if event.name == "response_account" and "summary" in event.data:
            acc = event.data["summary"]["address"]
            self.accounts[acc]["public_key"] = keys.PublicKey(bytes.fromhex(event.data["summary"]["publicKey"]))
            if "token" in event.data:
                self.accounts[acc]["balance"] = int(event.data["token"]["balance"])
            if "sequence" in event.data:
                self.accounts[acc]["nonce"] = int(event.data["sequence"]["nonce"])

               
class PasswordPrompt(urwid.LineBox):
    def __init__(self, ok_callback: Callable[[str], None], cancel_callback: Callable[[], None]):
        self.ok_callback = ok_callback
        self.cancel_callback = cancel_callback

        header_text = urwid.Text(('banner', 'Password'), align = 'center')
        header = urwid.AttrMap(header_text, 'banner')

        self.pwd_edit = urwid.Edit("$ ", mask="*")
        body_filler = urwid.Filler(self.pwd_edit, valign = 'top')
        body_padding = urwid.Padding(
            body_filler,
            left = 1,
            right = 1
        )
        body = urwid.LineBox(body_padding)

        footer = urwid.Columns([
            urwid.LineBox(attr_button("OK", on_press = self.ok, borders=False)), 
            urwid.LineBox(attr_button("Cancel", on_press = self.cancel, borders=False))
        ])

        _widgets = [("pack", header), body, ("pack", footer)]
        super().__init__(frames.UiPile(_widgets, focus_item=2))

    def ok(self, btn):
        pwd = self.pwd_edit.get_edit_text()
        self.ok_callback(pwd)
    
    def cancel(self, btn):
        self.cancel_callback()


class SendPrompt(urwid.LineBox):
    def __init__(self, ok_callback: Callable[[dict], None], cancel_callback: Callable[[], None]):
        self.ok_callback = ok_callback
        self.cancel_callback = cancel_callback

        header_text = urwid.Text(('banner', 'Send'), align = 'center')
        header = urwid.AttrMap(header_text, 'banner')

        self.recipient_edit = urwid.Edit("Recipient: ")
        self.amount_edit = urwid.IntEdit("Amount: ")
        self.data_edit = urwid.Edit("Data: ")
        self.fee_edit = urwid.IntEdit("Fee: ", default = int(0.5 * LSK))
        self.pwd_edit = urwid.Edit("Password: ", mask="*")
        params = urwid.ListBox(urwid.SimpleFocusListWalker([
            self.recipient_edit,
            urwid.Text(""),
            self.amount_edit,
            urwid.Text(""),
            self.data_edit,
            urwid.Text(""),
            self.fee_edit,
            urwid.Text(""),
            self.pwd_edit
        ]))
        body = urwid.LineBox(params)

        footer = urwid.Columns([
            urwid.LineBox(attr_button("OK", on_press = self.ok, borders=False)), 
            urwid.LineBox(attr_button("Cancel", on_press = self.cancel, borders=False))
        ])

        _widgets = [("pack", header), body, ("pack", footer)]
        super().__init__(frames.UiPile(_widgets, focus_item=2))

    def ok(self, btn):
        params = {
            "recipientAddress": self.recipient_edit.get_edit_text(),
            "amount": self.amount_edit.value(),
            "data": self.data_edit.get_edit_text(),
            "fee": self.fee_edit.value(),
            "pwd": self.pwd_edit.get_edit_text()
        }

        self.ok_callback(params)
    
    def cancel(self, btn):
        self.cancel_callback()

