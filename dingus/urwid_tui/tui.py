import urwid
import time
import os
import logging
import traceback

import dingus.component as component
import dingus.urwid_tui.frames as frames
from dingus.urwid_tui.utils import PALETTE, WIDTH, HEIGHT, create_button, terminal_size, attr_button, rgb_list_to_text
from dingus.types.event import Event
import dingus.utils as utils
from dingus.constants import LSK
import dingus.types.keys as keys


class TUI(component.ComponentMixin, urwid.Pile):
    def __init__(self, logger) -> None:
        self.logger = logger
        self.events = []
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

    def _exception_handler(self, loop, context):
        self.stop()
        exc = context.get('exception')
        print(traceback.format_exc())
        print(type(exc), exc, exc.__traceback__)
 
        if exc:
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
        btn_width = max(8, terminal_size()[0]//len(opts))
        for opt in opts:
            btn = create_button(opt, borders=False)
            urwid.connect_signal(btn, 'click', lambda btn, name=opt.lower(): self.parent.update_active_body(name))
            btn = urwid.AttrMap(btn, None, focus_map="line")
            _menu.append((btn_width, urwid.LineBox(btn)))

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
        new_act_btn = create_button("New", borders=False)
        urwid.connect_signal(new_act_btn, 'click', self.new_account)
        new_act_btn = urwid.AttrMap(new_act_btn, None, focus_map="line")
        self.select_act_btn = create_button("Change", borders=False)
        urwid.connect_signal(self.select_act_btn, 'click', self.select_account)
        select_act_btn = urwid.AttrMap(self.select_act_btn, None, focus_map="line")
        _btns = urwid.Columns([urwid.LineBox(select_act_btn), urwid.LineBox(new_act_btn)])
        
        _header = urwid.LineBox(urwid.Text(""))
        _widgets = [("pack", _header), ("pack", _btns), urwid.ListBox(urwid.SimpleFocusListWalker([]))]
        super().__init__(_widgets, **kwargs)
        self.current_account = None
        self.account_balance = 0
        self.update_body()

    def update_body(self):
        accounts = os.listdir("dingus/accounts")
        self.select_act_btn.disabled = bool(len(accounts) <= 1)
        
        if not accounts:
            header_data = urwid.Text("No account data, create a new one first.", align= "center")
            body_data = [urwid.Text("")]
        elif not self.current_account:
            self.current_account = accounts[0]

        if self.current_account:
            try:
                pk = keys.PrivateKey.from_json(self.current_account)
                public_key = pk.to_public_key().encode().hex()
                address = pk.to_public_key().to_address().to_lsk32()
                avatar = rgb_list_to_text(pk.to_public_key().to_address().to_avatar())
                btn = attr_button(["\n"] + avatar + ["\ncopy"], borders=False, on_press=lambda btn : utils.copy_to_clipboard(address))
                header_data = urwid.Columns([(16, btn), urwid.Text(f"\n{address}\n\n{self.account_balance} LSK", align="center")])
                body_data = [urwid.Text(f"Public key: {public_key}")]
            except Exception as e:
                input(e)
                header_data = urwid.Text("Invalid account file.", align= "center")
                body_data = [urwid.Text("")]
       
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(body_data))
        self.contents[0] = (urwid.LineBox(header_data), ("pack", None))
        self.contents[2] = (_body, ("weight", 1))

    def new_account(self, btn) -> None:
        sk = utils.random_private_key()
        sk.to_json()
        self.update_body()
    
    def select_account(self, btn) -> None:
        def select(btn, acc):
            self.current_account = acc
            self.update_body()

        accounts = os.listdir("dingus/accounts")
        body_data = []
        for filename in accounts:
            pk = keys.PrivateKey.from_json(filename)
            public_key = pk.to_public_key().encode().hex()
            address = pk.to_public_key().to_address().to_lsk32()
            avatar = rgb_list_to_text(pk.to_public_key().to_address().to_avatar())
            btn = attr_button(["\n"] + avatar + ["\nselect"], borders=False, on_press=lambda btn, acc=filename : select(btn, acc))
            body_data.append(urwid.Columns([(16, btn), urwid.Text(f"\n{address}", align="center")]))
            self.parent.emit_event("request_account", {"public_key" : pk.to_public_key().encode().hex()}, ["user_input"])
        
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(body_data))
        self.contents[2] = (_body, ("weight", 1))


    async def handle_event(self, event: Event) -> None:
        if event.name == "response_account":
            if "token" in event.data:
                self.account_balance = float(event.data["token"]["balance"]) / LSK
            else:
                self.account_balance = 0

               
        

        
