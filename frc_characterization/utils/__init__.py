from tkinter import *
from tkinter.constants import VERTICAL, RIGHT, LEFT, BOTH, END, Y


def validateInt(P):
    if str.isdigit(P) or P == "":
        return True
    else:
        return False


def validateFloat(P):
    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    if isfloat(P) or P == "":
        return True
    else:
        return False


class IntEntry(Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, validate="all")
        self["validatecommand"] = (self.register(validateInt), "%P")


class FloatEntry(Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, validate="all")
        self["validatecommand"] = (self.register(validateFloat), "%P")


class TextExtension(Frame):
    """Extends Frame.  Intended as a container for a Text field.  Better related data handling
    and has Y scrollbar."""

    def __init__(self, master, textvariable=None, *args, **kwargs):

        super(TextExtension, self).__init__(master)
        # Init GUI

        self._y_scrollbar = Scrollbar(self, orient=VERTICAL)

        self._text_widget = Text(
            self, yscrollcommand=self._y_scrollbar.set, *args, **kwargs
        )
        self._text_widget.pack(side=LEFT, fill=BOTH, expand=1)

        self._y_scrollbar.config(command=self._text_widget.yview)
        self._y_scrollbar.pack(side=RIGHT, fill=Y)

        if textvariable is not None:
            if not (isinstance(textvariable, Variable)):
                raise TypeError(
                    "tkinter.Variable type expected, "
                    + str(type(textvariable))
                    + " given.".format(type(textvariable))
                )
            self._text_variable = textvariable
            self.var_modified()
            self._text_trace = self._text_widget.bind(
                "<<Modified>>", self.text_modified
            )
            self._var_trace = textvariable.trace("w", self.var_modified)

    def text_modified(self, *args):
        if self._text_variable is not None:
            self._text_variable.trace_vdelete("w", self._var_trace)
            self._text_variable.set(self._text_widget.get(1.0, END))
            self._var_trace = self._text_variable.trace("w", self.var_modified)
            self._text_widget.edit_modified(False)

    def var_modified(self, *args):
        self.set_text(self._text_variable.get())
        self._text_widget.edit_modified(False)

    def unhook(self):
        if self._text_variable is not None:
            self._text_variable.trace_vdelete("w", self._var_trace)

    def clear(self):
        self._text_widget.delete(1.0, END)

    def set_text(self, _value):
        self.clear()
        if _value is not None:
            self._text_widget.insert(END, _value)
