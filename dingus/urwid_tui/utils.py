import urwid
import logging
import collections

WIDTH = 64
HEIGHT = 24

PALETTE = [
    ("line", "black", "white", "standout"),
    ("top", "white", "black"),
    ("black", "black", "black"),
    ("background", "white", "black"),
    ("background_focus", "black", "white", "standout"),
    ("name", "yellow", "black"),
    ("green", "light green", "black"),
    ("yellow", "yellow", "black"),
    ("red", "light red", "black")
]


class ButtonLabel(urwid.SelectableIcon):
    def set_text(self, label):
        '''
        set_text is invoked by Button.set_label
        '''
        self.__super.set_text(label)
        self._cursor_position = -1


class MyButton(urwid.Button):
    '''
    - override __init__ to use our ButtonLabel instead of urwid.SelectableIcon

    - make button_left and button_right plain strings and variable width -
      any string, including an empty string, can be set and displayed

    - otherwise, we leave Button behaviour unchanged
    '''
    button_left = "["
    button_right = "]"

    def __init__(self, label, on_press=None, user_args=None, borders=True, disabled=False):
        self._label = ButtonLabel("")
        if borders:
            cols = urwid.Columns([
                ('fixed', len(self.button_left), urwid.Text(self.button_left)),
                self._label,
                ('fixed', len(self.button_right), urwid.Text(self.button_right))],
                dividechars=1)
        else:
            cols = urwid.Columns([self._label],
                                 dividechars=0)

        super(urwid.Button, self).__init__(cols)

        self.disabled = disabled
        if on_press:
            urwid.connect_signal(self, "click", on_press, user_args=user_args)

        self.set_label(label)
        self.lllavel = label

    def selectable(self):
        return not self.disabled


def terminal_size(scr=urwid.raw_display.Screen()):
    return scr.get_cols_rows()


def attr_button(label, attr_map=None, focus_map="line", **kwargs):
    btn = create_button(label, **kwargs)
    return urwid.AttrMap(btn, attr_map, focus_map=focus_map)


def create_button(label, align="center", **kwargs):
    btn = MyButton(label, **kwargs)
    btn._label.align = align
    return btn


def combine_RGB_colors(color1, color2, weight1=1, weight2=1):
    return (int((color1[i] * weight1 + color2[i] * weight2) / (weight1 + weight2)) for i in range(3))


def RGBA_to_RGB(r, g, b, a, background=None):
    """
    apply alpha using only RGB channels: https://en.wikipedia.org/wiki/Alpha_compositing
    """
    if background:
        return combine_RGB_colors((r, g, b), background, weight1=a, weight2=255 * (255 - a))
    elif a == 255:
        return (r, g, b)
    return (int(c * a / 255.0) for c in (r, g, b))


def interpolate_colors(color1, color2, value):
    return [int(round(x + (y - x) * value)) for x, y in zip(color1, color2)]

def rgb_list_to_text(rgb_list: list[tuple[int]]) -> str:
    text = []
    w = h = int(len(rgb_list)**0.5)
    for y in range(h):
        for x in range(w):
            r, g, b = rgb_list[x + y * w]
            attr = f"#{r:02x}{g:02x}{b:02x}"
            text.append((urwid.AttrSpec(attr, attr, colors=256), "  "))
        text.append("\n")

    return text
