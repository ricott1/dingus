import urwid
import time
import dingus.urwid_tui.frames as frames
from dingus.urwid_tui.utils import WIDTH, HEIGHT, terminal_size

class TUI(frames.UiFrame):
    def __init__(self, event_loop) -> None:
        self.event_loop = event_loop
        self.warning_frame = frames.WarningFrame()
        _title = urwid.BoxAdapter(frames.TitleFrame(["Dingus"]), height=12)
        self.bottom = urwid.SolidFill("#")
        _body = urwid.Overlay(RecentBlocks(), self.bottom, "center", WIDTH, "middle", HEIGHT)
        super().__init__(_body, header=_title)


        self.loop = urwid.MainLoop(self, event_loop=urwid.AsyncioEventLoop(loop=event_loop))
        self.loop.unhandled_input = self.handle_input
    
    @property
    def active_body(self) -> frames.UiFrame:
        return self.contents["body"][0].contents[1][0]

    @active_body.setter
    def active_body(self, _body: frames.UiFrame) -> None:
        _body = urwid.Overlay(_body, self.bottom, "center", WIDTH, "middle", HEIGHT)
        self.contents["body"] = (_body, None)

    def start(self):
        self.loop.start()
        self.event_loop.set_exception_handler(self.loop.event_loop._exception_handler)
    
    def stop(self):
        self.loop.screen.stop()
        self.loop.stop()

    def handle_input(self, _input: str, pressed_since: float = 0) -> None:
        self.active_body.handle_input(_input, pressed_since)

    def on_update(self, _deltatime: float) -> None:
        cols, rows = terminal_size()
        if cols < WIDTH or rows < HEIGHT:
            if self.active_body is not self.warning_frame:
                self.suspended_body = self.active_body
                self.active_body = self.warning_frame
        else:
            if self.active_body is self.warning_frame:
                self.active_body = self.suspended_body
            self.active_body.on_update(_deltatime)
    
    def handle_event(self, event: dict) -> None:
        self.active_body.handle_event(event)


class RecentBlocks(frames.UiFrame):
    def __init__(self, **kwargs) -> None:
        _body = urwid.ListBox(urwid.SimpleFocusListWalker([urwid.Text("\n  Fetching new blocks...")]))
        super().__init__(_body, **kwargs)
    
    def update_block_data(self, block_data: dict) -> None:
        _block_data_list = [urwid.Text(f"\n  {k}: {v}") for k, v in block_data.items()]
        _body = urwid.ListBox(urwid.SimpleFocusListWalker(_block_data_list))
        self.contents["body"] = (_body, None)
    
    def handle_event(self, event: dict) -> None:
        if event["name"] == "new_block":
           self.update_block_data(event["data"])
        # elif event["name"] == "new_block":
        #    self.update_block_data(event["data"])

        