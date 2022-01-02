import urwid
import time

from dingus.urwid_tui.utils import create_button, attr_button, WIDTH, HEIGHT
from dingus.types.event import Event

MIN_HEADER_HEIGHT = 3
MAX_MENU_WIDTH = 48
FOOTER_HEIGHT = 4


class UiFrame(urwid.Frame):
    def __init__(self, body, **kwargs):
        super().__init__(body, **kwargs)

    def handle_input(self, _input: str, pressed_since: float=0) -> None:
        pass

    async def on_update(self, deltatime: float) -> None:
        pass

    async def handle_event(self, event: Event):
        pass

class UiPile(urwid.Pile):
    def __init__(self, widgets, **kwargs):
        super().__init__(widgets, **kwargs)

    def handle_input(self, _input: str, pressed_since: float=0) -> None:
        pass

    async def on_update(self, deltatime: float) -> None:
        pass

    async def handle_event(self, event: Event):
        pass

class WarningFrame(UiFrame):
    def __init__(self):
        super().__init__(urwid.ListBox(
            [urwid.Text(f"Please set terminal size to a minimum of {WIDTH}x{HEIGHT}")]))

class SplitHorizontalFrame(UiFrame):
    def __init__(self, widgets, weights=None, update_order=None, focus_column=None):
        self.widgets = widgets
        if not update_order:
            update_order = [i for i in range(len(self.widgets))]
        self.update_order = update_order
        if weights:
            super().__init__(urwid.Columns([('weight', weights[i], self.widgets[i]) for i in range(
                len(weights))], focus_column=focus_column))
        else:
            super().__init__(urwid.Columns(self.widgets, focus_column=focus_column))

    def on_update(self, deltatime):
        for index in self.update_order:
            if hasattr(self.widgets[index], "on_update"):
                self.widgets[index].on_update(deltatime)

    def handle_input(self, _input, pressed_since=0):
        for index in self.update_order:
            if hasattr(self.widgets[index], "handle_input"):
                self.widgets[index].handle_input(_input)


class SplitVerticalFrame(UiFrame):
    def __init__(self, widgets, weights=None, update_order=None, focus_item=None):
        self.widgets = widgets
        if not update_order:
            update_order = [i for i in range(len(self.widgets))]
        self.update_order = update_order
        if weights:
            super().__init__(urwid.Pile([('weight', weights[i], self.widgets[i]) for i in range(
                len(weights))], focus_item=focus_item))
        else:
            super().__init__(urwid.Pile(self.widgets, focus_item=focus_item))

    def on_update(self, deltatime):
        for index in self.update_order:
            if hasattr(self.widgets[index], "on_update"):
                self.widgets[index].on_update(deltatime)

    def handle_input(self, _input, pressed_since=0):
        for index in self.update_order:
            if hasattr(self.widgets[index], "handle_input"):
                self.widgets[index].handle_input(_input)


class TitleFrame(UiFrame):
    def __init__(self, _title, _attribute=None, _font=urwid.HalfBlock7x7Font(), _lifespan=4):
        if _attribute:
            _title = [(_attribute, t) for t in _title]
        bigtext = urwid.Pile(
            [urwid.Padding(urwid.BigText(t, _font), 'center', None) for t in _title])

        bigtext = urwid.Filler(bigtext)
        self.lifespan = _lifespan
        super().__init__(bigtext)
        self.start_time = time.time()


class OverlayFrame(UiFrame):
    def __init__(self, top, bottom, *args, top_linebox=True, **kwargs):
        self.top = top
        self.bottom = bottom
        if top_linebox:
            self.full_body = urwid.Overlay(urwid.LineBox(self.top), self.bottom, *args, **kwargs)
        else:
            self.full_body = urwid.Overlay(self.top, self.bottom, *args, **kwargs)

        super().__init__(self.full_body)
        self.top_is_visible = True

    def on_update(self, deltatime):
        self.top.on_update(deltatime)
        self.bottom.on_update(deltatime)

    def handle_input(self, _input):
        self.top.handle_input(_input)
        self.bottom.handle_input(_input)

    def toggle_top_view(self):
        if self.top_is_visible:
            self.contents["body"] = (self.bottom, None)
            self.top_is_visible = False
        else:
            self.contents["body"] = (self.full_body, None)
            self.top_is_visible = True


class TextFrame(UiFrame):
    def __init__(self, text=[""]):
        self.walker = urwid.SimpleFocusListWalker([urwid.Text(t) for t in text])
        listbox = urwid.ListBox(self.walker)
        super().__init__(listbox)

    def update(self, text):
        self.walker = urwid.SimpleFocusListWalker([urwid.Text(t) for t in text])


class EntryFrame(UiFrame):
    VERTICAL_OFFSET = 5

    def __init__(self, text, size=(20, 1), caption="", on_finish=None):
        self.entry = urwid.Edit(caption=caption)
        self.size = size
        self.selection = None
        super().__init__(urwid.ListBox([urwid.Text(
            "\n" * self.VERTICAL_OFFSET + text)]), footer=self.entry, focus_part="footer")

    def handle_input(self, _input, pressed_since=0):
        if _input == "enter":
            _name = self.entry.get_edit_text().strip()
            if len(_name) > 0:
                self.selection = _name
        else:
            self.keypress(self.size, _input)