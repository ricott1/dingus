import logging
import urwid
import traceback
import string
import os

import dingus.component as component
import dingus.transaction as transaction
import dingus.urwid_tui.prompts as prompts
from dingus.urwid_tui.utils import (
    PALETTE,
    WIDTH,
    HEIGHT,
    create_button,
    terminal_size,
    attr_button,
    avatar,
    TitleFrame,
)
from dingus.types.event import Event
import dingus.utils as utils
from dingus.constants import (
    LSK,
    BALANCE_TRANSFER_MAX_DATA_LENGTH,
    LISK32_ADDRESS_LENGTH,
    ID_STRING_LENGTH,
)
import dingus.types.keys as keys
from dingus.types.account import Account


class WarningFrame(urwid.Frame):
    def __init__(self) -> None:
        super().__init__(
            urwid.ListBox(
                [
                    urwid.Text(
                        f"Please set terminal size to a minimum of {WIDTH}x{HEIGHT}"
                    )
                ]
            )
        )


class TUI(component.ComponentMixin, urwid.Pile):
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = utils.get_accounts_from_files()
        self.on_account_change = []
        self.active_address = None

        self.warning_frame = WarningFrame()
        self.tip_header = CurrentTipLineBox(self)
        self.account_header = AccountInfo(self)
        self.bodies = {
            "greetings": urwid.WidgetDisable(TitleFrame(["Dingus"])),
            "explorer": Explorer(self),
            "selection": AccountSelection(self),
            "quitting": urwid.WidgetDisable(TitleFrame(["Good Bye"])),
            "empty": urwid.WidgetDisable(
                urwid.ListBox(urwid.SimpleFocusListWalker([]))
            ),
        }

        self.search_bar = SearchBarEdit(self)
        _footer = urwid.BoxAdapter(self.search_bar, height=3)
        super().__init__(
            [
                ("pack", self.tip_header),
                ("pack", self.account_header),
                self.bodies["greetings"],
                ("pack", _footer),
            ]
        )

    @property
    def active_body(self) -> urwid.Frame | urwid.Pile:
        return self.contents[2][0]

    @active_body.setter
    def active_body(self, _body: urwid.Frame | urwid.Pile) -> None:
        self.contents[2] = (_body, ("weight", 1))
        if hasattr(self.active_body, "start"):
            self.active_body.start()
        if _body in (
            self.bodies["empty"],
            self.bodies["greetings"],
            self.bodies["quitting"],
        ):
            self.focus_position = 1
        else:
            self.focus_position = 2

    @property
    def active_address(self) -> str | None:
        return self._active_address

    @active_address.setter
    def active_address(self, value: str) -> None:
        if not value or (value in self.accounts and value != self.active_address):
            self._active_address = value
            for callback in self.on_account_change:
                callback()

    def update_active_body(self, name: str) -> None:
        if name not in self.bodies:
            return

        if self.active_body != self.bodies[name]:
            self.active_body = self.bodies[name]

    def emit_explorer_event(
        self, event_name: str, event_data: dict, event_tags: list = ["user_input"]
    ) -> None:
        self.update_active_body("explorer")
        self.emit_event(event_name, event_data, event_tags)

    def set_widget_at(self, idx: int, widget) -> None:
        options = self.contents[idx][1]
        self.contents[idx] = (widget, options)

    async def start(self):
        print("Starting urwid loop")
        self.loop = urwid.MainLoop(
            self,
            palette=PALETTE,
            event_loop=urwid.AsyncioEventLoop(loop=self.event_loop),
        )
        self.loop.unhandled_input = self.handle_input
        self.loop.start()
        self.event_loop.set_exception_handler(self._exception_handler)

    def _exception_handler(self, loop, context):
        self.stop()
        exc = context.get("exception")
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

    async def handle_events(self, events: list[dict]) -> None:
        for event in events:
            if event.name == "network_status_update":
                await self.tip_header.handle_event(event)
            elif event.name == "response_block" or event.name == "response_account_explorer":
                await self.bodies["explorer"].handle_event(event)
            else:
                await self.account_header.handle_event(event)

    def handle_input(self, _input: str) -> None:
        if _input == "esc":
            self.quitting = True
            self.update_active_body("quitting")
        elif hasattr(self.active_body, "handle_input"):
            self.active_body.handle_input(_input)
        self.account_header.handle_input(_input)
        if self.focus_position == 3:
            self.search_bar.handle_input(_input)

    async def on_update(self, _deltatime: float) -> None:
        cols, rows = terminal_size()
        if cols < WIDTH or rows < HEIGHT:
            if self.active_body is not self.warning_frame:
                self.suspended_body = self.active_body
                self.active_body = self.warning_frame
        else:
            if self.active_body is self.warning_frame:
                self.active_body = self.suspended_body


class CurrentTipLineBox(urwid.LineBox):
    def __init__(self, parent: TUI) -> None:
        self.parent = parent
        self.walker = urwid.SimpleFocusListWalker(
            [urwid.Text("\n Fetching network status...", align="center")]
        )
        super().__init__(
            urwid.BoxAdapter(urwid.ListBox(self.walker), height=4),
            title=f"{os.environ['NETWORK']} status",
            title_attr="yellow",
        )

        self.initialized = False

    def selectable(self):
        return self.initialized

    def update(self, data: dict) -> None:

        if "data" not in data:
            return

        text = f"Current tip\nheight {data['data']['height']}"
        event_data_tip = {"key": "height", "value": data["data"]["height"]}
        tip_btn = attr_button(
            text,
            borders=False,
            on_press=lambda _: self.parent.emit_explorer_event(
                "request_block", event_data_tip
            ),
        )

        text = f"Last finalized\nheight {data['data']['finalizedHeight']}"
        event_data_fin = {
            "key": "height",
            "value": data["data"]["finalizedHeight"],
            "response_name": "response_block",
        }
        finalized_btn = attr_button(
            text,
            borders=False,
            on_press=lambda _: self.parent.emit_explorer_event(
                "request_block", event_data_fin
            ),
        )
        try:
            focus_position = int(self.body[0].focus_position)
        except:
            focus_position = 0

        self.walker[:] = [
            urwid.Columns([urwid.LineBox(finalized_btn), urwid.LineBox(tip_btn)])
        ]
        self.walker[0].focus_position = focus_position

        if not self.initialized:
            self.initialized = True

    async def handle_event(self, event: Event) -> None:
        self.update(event.data)


class SearchBarEdit(urwid.Frame):
    def __init__(self, parent: TUI) -> None:
        self.parent = parent
        self.search_edit = urwid.Edit(("yellow", "Search:"))
        urwid.connect_signal(self.search_edit, "change", self.update_edit_color)
        _body = urwid.ListBox(
            urwid.SimpleFocusListWalker([urwid.LineBox(self.search_edit)])
        )
        super().__init__(_body)

    def update_edit_color(self, edit: urwid.Edit, text: str):
        if (
            text.startswith("lsk")
            and len(text) == LISK32_ADDRESS_LENGTH
            and utils.validate_lisk32_address(text)
        ) or (
            len(text) == ID_STRING_LENGTH and all(c in string.hexdigits for c in text)
        ):
            self.search_edit.set_caption(("green", "Search:"))
        else:
            self.search_edit.set_caption(("yellow", "Search:"))

    def handle_input(self, _input: str) -> None:
        if _input == "enter":
            text = self.search_edit.get_edit_text()
            if (
                text.startswith("lsk")
                and len(text) == LISK32_ADDRESS_LENGTH
                and utils.validate_lisk32_address(text)
            ):
                self.parent.emit_explorer_event(
                    "request_account",
                    {
                        "key": "address",
                        "value": text,
                        "response_name": "response_account_explorer",
                    },
                )
                self.search_edit.edit_text = ""
            elif len(text) == ID_STRING_LENGTH and all(
                c in string.hexdigits for c in text
            ):
                self.parent.emit_explorer_event(
                    "request_block",
                    {
                        "key": "blockId",
                        "value": text,
                        "response_name": "response_block",
                    },
                )
                self.search_edit.edit_text = ""
        elif _input == "ctrl a":
            self.search_edit.edit_pos = 0
        elif _input == "ctrl k":
            self.search_edit.edit_text = self.search_edit.get_edit_text()[
                : self.search_edit.edit_pos
            ]
        elif _input == "ctrl u":
            self.search_edit.edit_text = ""


class AccountSelection(urwid.ListBox):
    def __init__(self, parent: TUI) -> None:
        self.parent = parent
        self.walker = urwid.SimpleFocusListWalker([urwid.Text("")])
        super().__init__(self.walker)

    def start(self):
        def select_btn(addr):
            self.parent.update_active_body("empty")
            self.parent.active_address = addr

        select_account_btns = []
        for address, account in self.parent.accounts.items():
            name = account.name

            btn = attr_button(
                ["\n"] + avatar(account.address) + ["\nselect"],
                borders=False,
                on_press=lambda _, acc=address: select_btn(acc),
            )
            selection_entry = urwid.Columns(
                [(16, btn), urwid.Text(f"\n{name}\n{address}", align="center")]
            )

            select_account_btns.append(selection_entry)

        self.walker[:] = urwid.SimpleFocusListWalker(select_account_btns)


class Explorer(urwid.ListBox):
    def __init__(self, parent: TUI) -> None:
        self.parent = parent
        _body = urwid.SimpleFocusListWalker([urwid.Text("")])
        super().__init__(_body)

    def display_block(self, data: dict) -> None:
        rows = [urwid.Text(("yellow", "\nBlock\n"), align="center")]
        label_length = max([len(k) for k in data.keys()]) + 3
        for k, v in data.items():
            btn = create_button(f"{v}", borders=False, align="left")
            if k == "previousBlockId":
                urwid.connect_signal(
                    btn,
                    "click",
                    lambda _, id=v: self.parent.emit_event(
                        "request_block",
                        {
                            "key": "blockId",
                            "value": id,
                            "response_name": "response_block",
                        },
                        ["user_input"],
                    ),
                )

            elif k == "maxHeightPreviouslyForged" or k == "maxHeightPrevoted":
                urwid.connect_signal(
                    btn,
                    "click",
                    lambda _, height=v: self.parent.emit_event(
                        "request_block",
                        {
                            "key": "height",
                            "value": height,
                            "response_name": "response_block",
                        },
                        ["user_input"],
                    ),
                )

            elif k == "generatorPublicKey":
                address = keys.PublicKey(bytes.fromhex(v)).to_address().to_lsk32()
                data = {
                    "key": "address",
                    "value": address,
                    "response_name": "response_account_explorer",
                }
                urwid.connect_signal(
                    btn,
                    "click",
                    lambda _, id=v: self.parent.emit_event(
                        "request_account", data, ["user_input"]
                    ),
                )

            elif k == "generatorUsername":
                data = {
                    "key": "username",
                    "value": v,
                    "response_name": "response_account_explorer",
                }
                urwid.connect_signal(
                    btn,
                    "click",
                    lambda _, id=v: self.parent.emit_event(
                        "request_account", data, ["user_input"]
                    ),
                )
            elif k == "generatorAddress":
                data = {
                    "key": "address",
                    "value": v,
                    "response_name": "response_account_explorer",
                }
                urwid.connect_signal(
                    btn,
                    "click",
                    lambda _, id=v: self.parent.emit_event(
                        "request_account", data, ["user_input"]
                    ),
                )

            btn = urwid.AttrMap(btn, None, focus_map="line")
            label = urwid.Text(("green", f" {k}: "))
            col = urwid.Columns([(label_length, label), btn])
            rows.append(col)

        self.body[:] = rows

    def display_account(self, data: dict) -> None:
        rows = [urwid.Text(("yellow", "\nAccount\n"), align="center")]
        label_length = max([len(k) for k in data["summary"].keys()]) + 3
        for k, v in data["summary"].items():
            btn = create_button(f"{v}", borders=False, align="left")
            btn = urwid.AttrMap(btn, None, focus_map="line")
            label = urwid.Text(("green", f" {k}: "))
            col = urwid.Columns([(label_length, label), btn])
            rows.append(col)

        self.body[:] = rows

    async def handle_event(self, event: Event) -> None:
        if event.name == "response_block":
            self.display_block(event.data)
        elif event.name == "response_account_explorer":
            self.display_account(event.data)


class AccountInfo(urwid.Pile):
    def __init__(self, parent: TUI) -> None:
        self.parent = parent

        new_act_btn = attr_button(
            "\n(N)ew\n", borders=False, on_press=self.prompt_new_account
        )

        select_act_btn = attr_button(
            f"\n(S)elect\n", borders=False, on_press=self.select_account
        )
        self.selecting_account = False

        import_act_btn = attr_button(
            f"\n(I)mport\n", borders=False, on_press=self.prompt_import_account
        )

        bookmark_act_btn = attr_button(
            f"\n(B)ookmark\n", borders=False, on_press=self.prompt_bookmark_account
        )

        _btns = urwid.Columns(
            [
                urwid.LineBox(select_act_btn),
                urwid.LineBox(new_act_btn),
                urwid.LineBox(import_act_btn),
                urwid.LineBox(bookmark_act_btn),
            ]
        )

        _header = urwid.LineBox(urwid.Text(""), title="Account")

        self.send_btn = attr_button(
            ["\nSend LSK\n"], borders=False, on_press=self.prompt_send_lsk
        )

        self.remove_account_btn = attr_button(
            ["\nRemove\n"], borders=False, on_press=self.remove_account
        )

        _widgets = [_header, ("pack", _btns)]
        super().__init__(_widgets)
        self.price_feeds = {"LSK_EUR": 0, "LSK_BTC": 0}
        self.is_prompting = False

        if self.accounts:
            self.parent.active_address = list(self.accounts.keys())[0]
        else:
            self.parent.active_address = None
        self.update_header()
        self.parent.on_account_change.append(self.on_account_change)

    @property
    def accounts(self) -> dict[str, Account]:
        return self.parent.accounts

    @accounts.setter
    def accounts(self, value: dict[str, Account]) -> dict[str, Account]:
        self.parent.accounts = value

    @property
    def active_address(self) -> str | None:
        return self.parent.active_address

    @active_address.setter
    def active_address(self, value: str) -> None:
        self.parent.active_address = value

    @property
    def active_account(self) -> Account | None:
        if not self.active_address:
            return None

        return self.accounts[self.active_address]

    def selectable(self) -> None:
        return not self.is_prompting

    def on_account_change(self) -> None:
        if self.active_address:
            event_data = {
                "key": "address",
                "value": self.active_address,
                "response_name": "response_account_info",
            }
            self.parent.emit_event("request_account", event_data, ["user_input"])
        self.update_header()

    def handle_input(self, _input: str) -> None:
        if self.is_prompting:
            return
        if _input in ("s", "S"):
            self.select_account()
        elif _input in ("n", "N"):
            self.prompt_new_account()
        elif _input in ("i", "I"):
            self.prompt_import_account()
        elif _input in ("b", "B"):
            self.prompt_bookmark_account()
        elif _input in ("c", "C"):
            if self.active_address:
                utils.copy_to_clipboard(self.active_address)

    def update_header(self) -> None:
        if not self.active_account:
            header_data = urwid.Text(
                "\n\n\n\nNo account data, create a new one first.\n\n\n\n\n",
                align="center",
            )
            title = ""
        else:
            btn = attr_button(
                ["\n\n"] + avatar(self.active_account.address) + ["\n(C)opy\n\n"],
                borders=False,
                on_press=lambda _: utils.copy_to_clipboard(self.active_address),
            )

            event_data = {
                "key": "address",
                "value": self.active_address,
                "response_name": "response_account_explorer",
            }

            top = urwid.LineBox(
                attr_button(
                    f"\n{self.active_address}\n",
                    borders=False,
                    on_press=lambda _: self.parent.emit_explorer_event(
                        "request_account", event_data
                    ),
                )
            )

            balance = float(self.active_account.balance) / LSK
            lsk_to_eur = balance * self.price_feeds["LSK_EUR"]
            lsk_to_btc = balance * self.price_feeds["LSK_BTC"]
            balances = urwid.Text(
                f"\n{balance} LSK\n{lsk_to_eur:.2f} EUR\n {lsk_to_btc:.8f} BTC",
                align="center",
            )

            if self.active_account.bookmark:
                bottom = urwid.Columns(
                    [urwid.LineBox(self.remove_account_btn), balances]
                )
            else:
                bottom = urwid.Columns([urwid.LineBox(self.send_btn), balances])

            header_data = urwid.Columns([(16, btn), urwid.Pile([top, bottom])])
            title = self.active_account.name

        self.contents[0] = (
            urwid.LineBox(header_data, title=title, title_attr="yellow"),
            ("pack", None),
        )

    def prompt_send_lsk(self, btn=None) -> None:
        if not self.active_address:
            return
        bottom_w = urwid.WidgetDisable(self.parent.active_body)
        top_w = prompts.SendPrompt(self.send_lsk, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 60, ("relative", 15), 20)
        self.parent.active_body = _overlay

    def send_lsk(self, params: dict) -> None:
        if not self.active_address:
            return
        if self.active_account.bookmark:
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
            self.prompt_text(
                f"Data exceeds maximum length. {len(params['data'])} > {BALANCE_TRANSFER_MAX_DATA_LENGTH}."
            )
            return

        tx_params = {
            "moduleID": bytes.fromhex("02"),
            "commandID": bytes.fromhex("00"),
            "senderPublicKey": self.active_account.public_key.hexbytes(),
            "nonce": self.active_account.nonce,
            "fee": int(fee * LSK),
            "asset": {
                "amount": int(amount * LSK),
                "recipientAddress": utils.get_address_from_lisk32_address(
                    params["recipientAddress"]
                ),
                "data": params["data"],
            },
        }

        trs = transaction.Transaction.from_dict(tx_params)
        logging.info(f"Sending transaction {trs}")

        try:
            filename = self.active_address + ".json"
            private_key = keys.PrivateKey.from_file(filename, params["password"])
            trs.sign(private_key)
            result = trs.send()
        except Exception as e:
            self.prompt_text(f"Error: {e}")
            return

        if "error" in result:
            self.prompt_text(
                f"Transaction {trs.id.hex()} errored!\n{result['message']}",
                title="Error",
            )
        else:
            # Increase nonce here in case user send multiple transaction
            # within one block. Real value will be overwritten on next block.
            self.active_account.nonce += 1
            self.prompt_text(f"Transaction {trs.id.hex()} sent!", title="Success")

    def destroy_prompt(self) -> None:
        self.parent.update_active_body("empty")
        self.is_prompting = False

    def prompt_text(
        self, text: str = "There was an error", title: str = "Error"
    ) -> None:
        bottom_w = urwid.WidgetDisable(self.parent.active_body)
        top_w = prompts.TextPrompt(text, title, self.destroy_prompt)
        _width = 48
        _height = 16 + len(text) // _width
        _overlay = urwid.Overlay(
            top_w, bottom_w, "center", _width, ("relative", 15), _height
        )
        self.parent.active_body = _overlay
        self.is_prompting = True

    def prompt_new_account(self, btn=None) -> None:
        bottom_w = urwid.WidgetDisable(self.parent.active_body)
        top_w = prompts.NewAccountPrompt(self.create_new_account, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 48, ("relative", 15), 13)
        self.parent.active_body = _overlay
        self.is_prompting = True

    def create_new_account(self, name: str, password: str) -> None:
        sk = utils.random_private_key()
        data = sk.encrypt(password)
        public_key = sk.to_public_key()
        address = public_key.to_address().to_lsk32()

        data["name"] = name
        data["address"] = address
        data["public_key"] = public_key
        filename = f"{address}.json"
        account = Account.from_dict(data)
        account.save(filename)
        self.accounts[address] = account
        self.active_address = address
        self.destroy_prompt()

    def prompt_import_account(self, btn=None) -> None:
        bottom_w = urwid.WidgetDisable(self.parent.active_body)
        top_w = prompts.ImportPrompt(self.import_account, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 60, ("relative", 15), 19)
        self.parent.active_body = _overlay
        self.is_prompting = True

    def import_account(self, name: str, password: str, passphrase: str) -> None:
        sk = keys.PrivateKey.from_passphrase(passphrase)
        public_key = sk.to_public_key()
        address = public_key.to_address().to_lsk32()
        if address in self.accounts:
            self.prompt_text("Address already imported.")
            return

        data = sk.encrypt(password)
        data["name"] = name
        data["address"] = address
        data["public_key"] = public_key
        filename = f"{address}.json"
        account = Account.from_dict(data)
        account.save(filename)

        self.accounts[address] = account
        self.active_address = address
        self.destroy_prompt()

    def prompt_bookmark_account(self, btn=None) -> None:
        bottom_w = urwid.WidgetDisable(self.parent.active_body)
        top_w = prompts.BookmarkPrompt(self.bookmark_account, self.destroy_prompt)
        _overlay = urwid.Overlay(top_w, bottom_w, "center", 48, ("relative", 15), 13)
        self.parent.active_body = _overlay
        self.is_prompting = True

    def bookmark_account(self, name: str, address: str) -> None:
        if not utils.validate_lisk32_address(address):
            self.prompt_text("Invalid lsk address")
            return

        if address in self.accounts:
            self.prompt_text("Address already followed.")
            return

        data = {"name": name, "address": address, "bookmark": True}
        filename = f"bookmark.{address}.json"
        account = Account.from_dict(data)
        account.save(filename)

        self.accounts[address] = account
        self.active_address = address
        self.destroy_prompt()

    def remove_account(self, btn=None) -> None:
        filename = f"{self.active_address}.json"
        if self.active_account.bookmark:
            filename = "bookmark." + filename
        utils.delete_account(filename)
        del self.accounts[self.active_address]
        if self.accounts:
            self.active_address = list(self.accounts.keys())[0]
        else:
            self.active_address = None

    def select_account(self, btn=None) -> None:
        if self.selecting_account:
            self.selecting_account = False
            self.parent.update_active_body("empty")
        else:
            self.selecting_account = True
            self.parent.update_active_body("selection")

    async def handle_event(self, event: dict) -> None:
        if event.name == "response_account" and self.active_account:
            self.update(self.active_account)
        elif event.name == "network_status_update":
            data = {
                "key": "address",
                "value": self.active_address,
                "response_name": "response_account_info",
            }
            self.parent.emit_event("request_account", data, ["user_input"])
        elif event.name == "market_prices_update":
            if event.data:
                for feed in event.data:
                    self.price_feeds[feed["code"]] = float(feed["rate"])
                self.update_header()
        elif (
            event.name == "response_account_info"
            and "summary" in event.data
            and "address" in event.data["summary"]
        ):
            address: str = event.data["summary"]["address"]
            if address not in self.accounts:
                return

            account_changed = False
            if "publicKey" in event.data and event.data["summary"]["publicKey"]:
                public_key = keys.PublicKey(
                    bytes.fromhex(event.data["summary"]["publicKey"])
                )
                if self.accounts[address].public_key != public_key:
                    self.accounts[address].public_key = public_key
                    account_changed = True
            if "token" in event.data:
                balance = int(event.data["token"]["balance"])
                if self.accounts[address].balance != balance:
                    self.accounts[address].balance = balance
                    account_changed = True
            if "sequence" in event.data:
                nonce = int(event.data["sequence"]["nonce"])
                if self.accounts[address].nonce != nonce:
                    self.accounts[address].nonce = nonce
                    account_changed = True
                self.accounts[address].nonce = int(event.data["sequence"]["nonce"])

            if account_changed:
                filename = f"{address}.json"
                # account_data = {k: v for k, v in self.accounts[address].items() if k not in ("avatar", "selection")}
                # account = Account.from_dict(account_data)
                self.accounts[address].save(filename)
                # self.accounts[address] = account


class TransactionsList(urwid.ListBox):
    def __init__(self, parent: TUI) -> None:
        self.parent = parent
        super().__init__([])
