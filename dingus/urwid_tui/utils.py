import urwid
import dingus.utils as utils
import dingus.crypto as crypto

WIDTH = 64
HEIGHT = 24

PALETTE = [
    ("line", "black", "white", "standout"),
    ("top", "white", ""),
    ("black", "black", "white"),
    ("background", "white", ""),
    ("background_focus", "black", "white", "standout"),
    ("green", "light green", ""),
    ("yellow", "yellow", ""),
    ("red", "light red", ""),
]


class ButtonLabel(urwid.SelectableIcon):
    def set_text(self, label):
        """
        set_text is invoked by Button.set_label
        """
        self.__super.set_text(label)
        self._cursor_position = -1


class MyButton(urwid.Button):
    """
    - override __init__ to use our ButtonLabel instead of urwid.SelectableIcon

    - make button_left and button_right plain strings and variable width -
      any string, including an empty string, can be set and displayed

    - otherwise, we leave Button behaviour unchanged
    """

    button_left = "["
    button_right = "]"

    def __init__(
        self, label, on_press=None, user_args=None, borders=True, disabled=False
    ):
        self._label = ButtonLabel("")
        if borders:
            cols = urwid.Columns(
                [
                    ("fixed", len(self.button_left), urwid.Text(self.button_left)),
                    self._label,
                    ("fixed", len(self.button_right), urwid.Text(self.button_right)),
                ],
                dividechars=1,
            )
        else:
            cols = urwid.Columns([self._label], dividechars=0)

        super(urwid.Button, self).__init__(cols)

        self.disabled = disabled
        if on_press:
            urwid.connect_signal(self, "click", on_press, user_args=user_args)

        self.set_label(label)
        self.lllavel = label

    def selectable(self):
        return not self.disabled


class TitleFrame(urwid.Frame):
    def __init__(self, _title, _attribute=None, _font=urwid.HalfBlock7x7Font()):
        if _attribute:
            _title = [(_attribute, t) for t in _title]
        bigtext = urwid.Pile(
            [urwid.Padding(urwid.BigText(t, _font), "center", None) for t in _title]
        )

        bigtext = urwid.Filler(bigtext)
        super().__init__(bigtext)


def terminal_size(scr=urwid.raw_display.Screen()):
    return scr.get_cols_rows()


def attr_button(label, attr_map=None, focus_map="line", **kwargs):
    btn = create_button(label, **kwargs)
    return urwid.AttrMap(btn, attr_map, focus_map=focus_map)


def create_button(label, align="center", **kwargs):
    btn = MyButton(label, **kwargs)
    btn._label.align = align
    return btn


def rgb_list_to_text(rgb_list: list[tuple[int]]) -> str:
    text = []
    w = h = int(len(rgb_list) ** 0.5)
    for y in range(h):
        for x in range(w):
            r, g, b = rgb_list[x + y * w]
            attr = f"#{r:02x}{g:02x}{b:02x}"
            text.append((urwid.AttrSpec(attr, attr, colors=256), "  "))
        text.append("\n")

    return text


def lisk32_to_avatar(base32_address: str) -> list[tuple[int]]:
    address = utils.get_address_from_lisk32_address(base32_address)
    avatar = []
    r, g, b = [crypto.hash(bytes.fromhex(f"0{i}") + address) for i in range(3)]
    color_bin_size = 32
    for i in range(0, len(r), 2):
        _r = int.from_bytes(r[i : i + 1], "big") // color_bin_size * color_bin_size
        _g = int.from_bytes(g[i : i + 1], "big") // color_bin_size * color_bin_size
        _b = int.from_bytes(b[i : i + 1], "big") // color_bin_size * color_bin_size
        avatar.append((_r, _g, _b))
    return avatar


def avatar(base32_address: str) -> str:
    return rgb_list_to_text(lisk32_to_avatar(base32_address))
