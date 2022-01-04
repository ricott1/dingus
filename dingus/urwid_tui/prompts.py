import urwid
from typing import Callable
import os

from dingus.urwid_tui.utils import attr_button
import dingus.urwid_tui.frames as frames
from dingus.constants import LSK

class TextPrompt(urwid.LineBox):
    def __init__(self, error_text: str, title: str, ok_callback: Callable[[], None]) -> None:
        self.ok_callback = ok_callback

        header_text = urwid.Text(('banner', title), align = 'center')
        header = urwid.AttrMap(header_text, 'banner')

        error = urwid.Text(error_text)
        body_filler = urwid.Filler(error, valign = 'top')
        body_padding = urwid.Padding(
            body_filler,
            left = 1,
            right = 1
        )
        body = urwid.LineBox(body_padding)

        footer = urwid.Columns([
            urwid.LineBox(attr_button("OK", on_press = self.ok, borders=False)), 
        ])

        _widgets = [("pack", header), body, ("pack", footer)]
        super().__init__(frames.UiPile(_widgets, focus_item=2))

    def ok(self, btn):
        self.ok_callback()

class PasswordPrompt(urwid.LineBox):
    def __init__(self, ok_callback: Callable[[str], None], cancel_callback: Callable[[], None]) -> None:
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
    def __init__(self, ok_callback: Callable[[dict], None], cancel_callback: Callable[[], None]) -> None:
        self.ok_callback = ok_callback
        self.cancel_callback = cancel_callback

        header_text = urwid.Text(('banner', 'Send'), align = 'center')
        header = urwid.AttrMap(header_text, 'banner')

        self.recipient_edit = urwid.Edit("Recipient: ")
        self.amount_edit = urwid.Edit("Amount: LSK ", edit_text="0")
        self.data_edit = urwid.Edit("Data: ")
        self.fee_edit = urwid.Edit("Fee: LSK ", edit_text = str(float(int(os.environ["DINGUS_MIN_FEE_PER_BYTE"]) / LSK)))
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
            "amount": self.amount_edit.get_edit_text(),
            "data": self.data_edit.get_edit_text(),
            "fee": self.fee_edit.get_edit_text(),
            "password": self.pwd_edit.get_edit_text()
        }

        self.ok_callback(params)
    
    def cancel(self, btn):
        self.cancel_callback()
