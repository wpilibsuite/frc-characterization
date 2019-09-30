import tkinter
from tkinter import *
from tkinter import filedialog

import os
import shutil

import importlib.resources as resources

import drive_characterization

from utils.utils import IntEntry
from utils.utils import FloatEntry


def configureGUI(STATE, mech):
    def getProjectLocation():
        file_path = filedialog.askdirectory(
            title='Choose the project location', initialdir=os.getcwd()
        )
        projLocationEntry.configure(state='normal')
        projLocationEntry.delete(0, END)
        projLocationEntry.insert(0, file_path)
        projLocationEntry.configure(state='readonly')

    def getConfigPath():
        file_path = tkinter.filedialog.askopenfilename(
            title='Choose the config file',
            initialdir=STATE.project_path.get(),
            filetypes=(('Python', '*.py'),),
        )
        configEntry.configure(state='normal')
        configEntry.delete(0, END)
        configEntry.insert(0, file_path)
        configEntry.configure(state='readonly')

    def genDefaultConfig():
        shutil.copy(
            src=os.path.join(templatePath, 'robotconfig.py'),
            dst=STATE.project_path.get(),
        )

    def updateTemplatePath(*args):
        nonlocal templatePath
        with resources.path(mech, 'templates') as path:
            templatePath = os.path.join(path, STATE.project_type.get())

    def updateConfigPath(*args):
        configEntry.configure(state='normal')
        STATE.config_path.set(os.path.join(STATE.project_path.get(), 'robotconfig.py'))
        configEntry.configure(state='readonly')

    def readConfig():
        try:
            with open(STATE.config_path.get(), 'r') as config:
                STATE.config = eval(config.read())
        except:
            tkinter.messagebox.showerror('Error!', 'Could not open/read config file.')
            return

        genProjButton.configure(state='normal')

    def genProject():
        dst = os.path.join(STATE.project_path.get(), 'characterization-project')
        with resources.path(mech, 'robot') as path:
            shutil.copytree(
                src=os.path.join(path, 'project-' + STATE.project_type.get()), dst=dst
            )
            with open(
                os.path.join(dst, 'src', 'main', 'java', 'dc', 'Robot.java'), 'w+'
            ) as robot:
                robot.write(mech.genRobotCode(STATE.project_type.get(), STATE.config))

    templatePath = None
    updateTemplatePath()

    # TOP OF WINDOW

    topFrame = Frame(STATE.mainGUI)
    topFrame.grid(row=0, column=0, sticky='ew')

    Button(topFrame, text='Select Project Location', command=getProjectLocation).grid(
        row=0, column=0, sticky='ew'
    )

    projLocationEntry = Entry(
        topFrame, textvariable=STATE.project_path, width=80, state='readonly'
    )
    projLocationEntry.grid(row=0, column=1, columnspan=10)
    STATE.project_path.trace_add('write', updateConfigPath)

    projectChoices = {'Simple', 'Talon'}
    projTypeMenu = OptionMenu(topFrame, STATE.project_type, *sorted(projectChoices))
    projTypeMenu.grid(row=0, column=11, sticky='ew')
    STATE.project_type.trace_add('write', updateTemplatePath)

    Button(topFrame, text='Select Config File', command=getConfigPath).grid(
        row=1, column=0, sticky='ew'
    )
    configEntry = Entry(
        topFrame, textvariable=STATE.config_path, width=80, state='readonly'
    )
    configEntry.grid(row=1, column=1, columnspan=10)

    Button(topFrame, text='Generate Default Config', command=genDefaultConfig).grid(
        row=1, column=11
    )

    for child in topFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    # Bottom Frame

    bottomFrame = Frame(STATE.mainGUI, bd=2, relief='groove')
    bottomFrame.grid(row=1, column=0, sticky='ew')

    readConfigButton = Button(bottomFrame, text='Read Config', command=readConfig)
    readConfigButton.grid(row=0, column=0, sticky='ew')

    genProjButton = Button(bottomFrame, text='Generate Project', command=genProject)
    genProjButton.grid(row=0, column=1, sticky='ew')
    genProjButton.configure(state='disabled')

    for child in bottomFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

class GuiState:
    def __init__(self):
        self.mainGUI = tkinter.Tk()

        self.project_path = StringVar()
        self.project_path.set(os.getcwd())

        self.config_path = StringVar()
        self.config_path.set(os.path.join(os.getcwd(), 'robotconfig.py'))

        self.project_type = StringVar()
        self.project_type.set('Simple')

        self.config = None


def main(mech):
    STATE = GuiState()

    configureGUI(STATE, mech)

    STATE.mainGUI.mainloop()


if __name__ == '__main__':

    main(drive_characterization)
