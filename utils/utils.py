import tkinter
from tkinter import *

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
        self["validatecommand"] = (self.register(validateInt), '%P')

class FloatEntry(Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, validate="all")
        self["validatecommand"] = (self.register(validateFloat), '%P')