import urwid
import time
import logging
import traceback

import dingus.component as component
import dingus.urwid_tui.frames as frames
from dingus.urwid_tui.utils import PALETTE, WIDTH, HEIGHT, create_button, terminal_size, attr_button
from dingus.types.event import Event


class TUI(component.ComponentMixin, urwid.Pile):
    def __init__(self, logger) -> None:
        self.logger = logger
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
    def active_body(self) -> frames.UiFrame:
        return self.contents[1][0]

    @active_body.setter
    def active_body(self, _body: frames.UiFrame) -> None:
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
        print(traceback.format_exc())
        exc = context.get('exception')
        if exc:
            if not isinstance(exc, urwid.ExitMainLoop):
                # Store the exc_info so we can re-raise after the loop stops
                urwid.compat.reraise(type(exc), exc, exc.__traceback__)
        else:
            loop.default_exception_handler(context)
        
    def stop(self):
        self.loop.stop()

    async def handle_event(self, event: dict) -> None:
        await self.active_body.handle_event(event)
        await self.base_header.handle_event(event)

    def handle_input(self, _input: str, pressed_since: float = 0) -> None:
        if _input in ("q", "Q", "esc"):
            self.emit_event("quit_input", {}, ["user_input"])
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
            await self.base_header.on_update(_deltatime)
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
        if event.name == "requested_block":
           self.update_block_data(event.data)
        
    async def on_update(self, event: dict) -> None:
        pass


class AccountInfo(frames.UiFrame):
    def __init__(self, parent, **kwargs) -> None:
        self.parent = parent
        _body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("\n  No account data")]))
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
        if event.name == "new_block":
           self.update_block_data(event.data)
        
    async def on_update(self, event: dict) -> None:
        pass
