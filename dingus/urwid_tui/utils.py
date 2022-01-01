import urwid
import logging
import collections

WIDTH = 96
HEIGHT = 40

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


class TailLogHandler(logging.Handler):

    def __init__(self, log_queue):
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.append(self.format(record))


class TailLogger(object):

    def __init__(self, maxlen):
        self._log_queue = collections.deque(maxlen=maxlen)
        self._log_handler = TailLogHandler(self._log_queue)

    def contents(self):
        return '\n'.join(self._log_queue)

    @property
    def log_handler(self):
        return self._log_handler

class SelectableColumns(urwid.Columns):
    def __init__(self, widget_list, focus_column=None, dividechars=0, on_keypress=None):
        super().__init__(widget_list, dividechars, focus_column)
        self.on_keypress = on_keypress

    def keypress(self, size, key):
        super().keypress(size, key)
        if self.on_keypress and key != "enter":
            self.on_keypress()

    def focus_next(self):
        try:
            self.focus_position += 1
        except ValueError:
            pass

    def focus_previous(self):
        try:
            self.focus_position -= 1
        except ValueError:
            pass


class ButtonLabel(urwid.SelectableIcon):
    def set_text(self, label):
        '''
        set_text is invoked by Button.set_label
        '''
        self.__super.set_text(label)
        self._cursor_position = len(label) + 1


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



def image_to_text(img, y_offset=0, x_offset=0, background=None):
    def pixel(x, y):
        r, g, b, a = img.get_at((x, y))
        if a > 0:
            r, g, b = RGBA_to_RGB(r, g, b, a, background=background)
            attr = f"#{r:02x}{g:02x}{b:02x}"
            return (urwid.AttrSpec(attr, attr, colors=256), "  ")
        return "  "

    text = ["\n" * y_offset]
    w, h = img.get_width(), img.get_height()
    for y in range(h):
        text.append("  " * x_offset)
        for x in range(w):
            text.append(pixel(x, y))
        text.append("\n")

    return text
