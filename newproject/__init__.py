import tkinter
from tkinter import *
from tkinter import filedialog

from subprocess import Popen, PIPE

import os
import shutil

import importlib.resources as resources

import drive_characterization

from utils.utils import IntEntry
from utils.utils import FloatEntry
from utils.utils import TextExtension

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

    def saveConfig():
        with open(STATE.config_path.get(), 'w+') as config:
            config.write(STATE.config.get())

    def updateTemplatePath(*args):
        nonlocal templatePath
        with resources.path(mech, 'templates') as path:
            templatePath = os.path.join(path, STATE.project_type.get())
        getDefaultConfig()

    def updateConfigPath(*args):
        configEntry.configure(state='normal')
        STATE.config_path.set(os.path.join(STATE.project_path.get(), 'robotconfig.py'))
        configEntry.configure(state='readonly')

    def getDefaultConfig():
        with open(os.path.join(templatePath, 'robotconfig.py'), 'r') as config:
            STATE.config.set(config.read())

    def readConfig():
        try:
            with open(STATE.config_path.get(), 'r') as config:
                STATE.config.set(config.read())
        except:
            tkinter.messagebox.showerror('Error!', 'Could not open/read config file.')
            return

    def genProject():
        dst = os.path.join(STATE.project_path.get(), 'characterization-project')
        with resources.path(mech, 'robot') as path:
            shutil.copytree(
                src=os.path.join(path, 'project-' + STATE.project_type.get()), dst=dst
            )
            with open(
                os.path.join(dst, 'src', 'main', 'java', 'dc', 'Robot.java'), 'w+'
            ) as robot:
                robot.write(mech.genRobotCode(STATE.project_type.get(), eval(STATE.config.get())))
            with open(os.path.join(dst, 'Build.gradle'), 'w+') as build:
                build.write(mech.genBuildGradle(STATE.project_type.get(), STATE.team_number.get()))

    def deployProject():
        os.chdir(os.path.join(STATE.project_path.get(), 'characterization-project'))
        if os.name == 'Windows':
            Popen([os.path.join(STATE.project_path.get(), 'characterization-project', 'gradlew.bat'), 'deploy'], stdin=PIPE)
        else:
            Popen([os.path.join(STATE.project_path.get(), 'characterization-project', 'gradlew'), 'deploy'], stdin=PIPE)


    templatePath = None
    updateTemplatePath()

    getDefaultConfig()

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

    Label(topFrame, text="Project Type:", anchor='e').grid(row=0, column=11, sticky='ew')

    projectChoices = {'Simple', 'Talon'}
    projTypeMenu = OptionMenu(topFrame, STATE.project_type, *sorted(projectChoices))
    projTypeMenu.grid(row=0, column=12, sticky='ew')
    STATE.project_type.trace_add('write', updateTemplatePath)

    Button(topFrame, text='Select Config File', command=getConfigPath).grid(
        row=1, column=0, sticky='ew'
    )
    configEntry = Entry(
        topFrame, textvariable=STATE.config_path, width=80, state='readonly'
    )
    configEntry.grid(row=1, column=1, columnspan=10)

    Button(topFrame, text='Save Config', command=saveConfig).grid(
        row=1, column=11
    )

    readConfigButton = Button(topFrame, text='Read Config', command=readConfig)
    readConfigButton.grid(row=1, column=12, sticky='ew')

    Label(topFrame, text='Team Number:', anchor='e').grid(row=2, column=0, sticky='ew')
    teamNumberEntry = IntEntry(topFrame, textvariable=STATE.team_number)
    teamNumberEntry.grid(row=2, column=1, sticky='ew')

    for child in topFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    # Body Frame

    bodyFrame = Frame(STATE.mainGUI, bd=2, relief='groove')
    bodyFrame.grid(row=1, column=0, sticky='ew')

    genProjButton = Button(bodyFrame, text='Generate Project', command=genProject)
    genProjButton.grid(row=1, column=0, sticky='ew')

    deployButton = Button(bodyFrame, text='Deploy Project', command=deployProject)
    deployButton.grid(row=2, column=0, sticky='ew')

    configEditPane = TextExtension(bodyFrame, textvariable=STATE.config)
    configEditPane.grid(row=0, column=1, rowspan=30, columnspan=10)

    

    for child in bodyFrame.winfo_children():
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

        self.config = StringVar()
    
        self.team_number = IntVar()


def main(mech):
    STATE = GuiState()

    configureGUI(STATE, mech)

    STATE.mainGUI.mainloop()


if __name__ == '__main__':

    main(drive_characterization)
