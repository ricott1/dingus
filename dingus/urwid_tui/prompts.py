import urwid
from typing import Callable, Any
import os

from dingus.urwid_tui.utils import attr_button
import dingus.urwid_tui.frames as frames
from dingus.constants import LSK, BALANCE_TRANSFER_LENGTH


class Prompt(urwid.LineBox):
    def __init__(self, title: str, body_widgets: list, ok_callback: Callable[[Any], None], cancel_callback: Callable[[Any], None] | None = None, focus_item:int = 2) -> None:
        self.ok_callback = ok_callback
        self.cancel_callback = cancel_callback

        header = urwid.Text(title + "\n", align = "center")

        footer_columns = [
            urwid.LineBox(attr_button("OK", on_press = self.ok, borders=False))
        ]
        if cancel_callback:
            footer_columns.append(
                urwid.LineBox(attr_button("Cancel", on_press = self.cancel, borders=False))
            )
        footer = urwid.Columns(footer_columns)

        _widgets = [("pack", header), *body_widgets, ("pack", footer)]
        super().__init__(
            frames.UiPile(_widgets, focus_item=focus_item),
            tlcorner = "╔", 
            tline = "═", 
            lline = "║", 
            trcorner = "╗", 
            blcorner = "╚", 
            rline = "║", 
            bline = "═", 
            brcorner = "╝"
        )
    
    def ok(self, btn):
        self.ok_callback()
    
    def cancel(self, btn):
        self.cancel_callback()

class TextPrompt(Prompt):
    def __init__(self, error_text: str, title: str, ok_callback: Callable[[], None]) -> None:

        error = urwid.Text(error_text)
        body_filler = urwid.Filler(error, valign = "top")
        body_padding = urwid.Padding(
            body_filler,
            left = 1,
            right = 1
        )
        body = urwid.LineBox(body_padding)

        super().__init__(title, [body], ok_callback)

    def ok(self, btn):
        self.ok_callback()

class NewAccountPrompt(Prompt):
    def __init__(self, ok_callback: Callable[[str, str], None], cancel_callback: Callable[[], None]) -> None:
        self.ok_callback = ok_callback
        self.cancel_callback = cancel_callback

        self.name_edit = urwid.Edit("", edit_text = "MyAccount #")
        name_filler = urwid.Filler(self.name_edit, valign = "top")
        name_padding = urwid.Padding(
            name_filler,
            left = 1,
            right = 1
        )
        name_body = urwid.LineBox(name_padding, title = "Name")

        self.pwd_edit = urwid.Edit("", mask="*")
        pwd_filler = urwid.Filler(self.pwd_edit, valign = "top")
        pwd_padding = urwid.Padding(
            pwd_filler,
            left = 1,
            right = 1
        )
        pwd_body = urwid.LineBox(pwd_padding, title = "Password")

        super().__init__(
            "New Account", 
            [name_body, pwd_body], 
            ok_callback, 
            cancel_callback = cancel_callback, 
            focus_item=1
        )

    def ok(self, btn):
        name = self.name_edit.get_edit_text()
        pwd = self.pwd_edit.get_edit_text()
        self.ok_callback(name, pwd)
    

class ImportPrompt(Prompt):
    def __init__(self, ok_callback: Callable[[str, str, str], None], cancel_callback: Callable[[], None]) -> None:
        self.name_edit = urwid.Edit("", edit_text = "MyAccount #")
        name_filler = urwid.Filler(self.name_edit, valign = "top")
        name_padding = urwid.Padding(
            name_filler,
            left = 1,
            right = 1
        )
        name_body = urwid.LineBox(name_padding, title = "Name")
        
        self.pwd_edit = urwid.Edit("", mask="*")
        pwd_filler = urwid.Filler(self.pwd_edit, valign = "top")
        pwd_padding = urwid.Padding(
            pwd_filler,
            left = 1,
            right = 1
        )
        pwd_body = urwid.LineBox(pwd_padding, title = "Password")

        self.passphrase_edit = urwid.Edit("", mask="*")
        passphrase_filler = urwid.Filler(self.passphrase_edit, valign = "top")
        passphrase_padding = urwid.Padding(
            passphrase_filler,
            left = 1,
            right = 1
        )
        passphrase_body = urwid.LineBox(passphrase_padding, title = "Passphrase")

        super().__init__(
            "Import Account", 
            [("weight", 1, name_body), ("weight", 2, passphrase_body), ("weight", 1, pwd_body)], 
            ok_callback, 
            cancel_callback = cancel_callback, 
            focus_item=1
        )

    def ok(self, btn):
        name = self.name_edit.get_edit_text()
        pwd = self.pwd_edit.get_edit_text()
        passphrase = self.passphrase_edit.get_edit_text()
        self.ok_callback(name, pwd, passphrase)


class BookmarkPrompt(Prompt):
    def __init__(self, ok_callback: Callable[[str, str], None], cancel_callback: Callable[[], None]) -> None:
        self.name_edit = urwid.Edit("", edit_text = "Bookmark #")
        name_filler = urwid.Filler(self.name_edit, valign = "top")
        name_padding = urwid.Padding(
            name_filler,
            left = 1,
            right = 1
        )
        name_body = urwid.LineBox(name_padding, title = "Name")

        self.address_edit = urwid.Edit("")
        body_filler = urwid.Filler(self.address_edit, valign = "top")
        body_padding = urwid.Padding(
            body_filler,
            left = 1,
            right = 1
        )
        body = urwid.LineBox(body_padding, title = "Address")

        super().__init__(
            "Bookmark", 
            [name_body, body], 
            ok_callback, 
            cancel_callback = cancel_callback, 
            focus_item=1
        )

    def ok(self, btn):
        name = self.name_edit.get_edit_text()
        address = self.address_edit.get_edit_text()
        self.ok_callback(name, address)
    

class SendPrompt(Prompt):
    def __init__(self, ok_callback: Callable[[dict], None], cancel_callback: Callable[[], None]) -> None:
        self.recipient_edit = urwid.Edit("Recipient: ")
        self.amount_edit = urwid.Edit("Amount: LSK ", edit_text="0")
        self.data_edit = urwid.Edit("Data: ")
        self.fee_edit = urwid.Edit("Fee: LSK ", edit_text = f"{float(BALANCE_TRANSFER_LENGTH *int(os.environ['DINGUS_MIN_FEE_PER_BYTE']) / LSK):.4f}")
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
        body = urwid.LineBox(params, title = "Parameters")

        super().__init__(
            "Send LSK", 
            [body], 
            ok_callback, 
            cancel_callback = cancel_callback, 
            focus_item=1
        )

    def ok(self, btn):
        params = {
            "recipientAddress": self.recipient_edit.get_edit_text(),
            "amount": self.amount_edit.get_edit_text(),
            "data": self.data_edit.get_edit_text(),
            "fee": self.fee_edit.get_edit_text(),
            "password": self.pwd_edit.get_edit_text()
        }

        self.ok_callback(params)
