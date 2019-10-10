import importlib.resources as resources
import os
import shutil
import tkinter
from subprocess import PIPE, Popen, STDOUT
from tkinter import *
from tkinter import filedialog
import tkinter.messagebox
from tkinter.scrolledtext import ScrolledText

import drive_characterization
from utils.utils import FloatEntry, IntEntry, TextExtension
import robot as res


def configureGUI(STATE, mech):
    def getProjectLocation():
        file_path = filedialog.askdirectory(
            title="Choose the project location", initialdir=STATE.project_path.get()
        )
        projLocationEntry.configure(state="normal")
        projLocationEntry.delete(0, END)
        projLocationEntry.insert(0, file_path)
        projLocationEntry.configure(state="readonly")

    def getConfigPath():
        file_path = tkinter.filedialog.askopenfilename(
            title="Choose the config file",
            initialdir=STATE.project_path.get(),
            filetypes=(("Python", "*.py"),),
        )
        configEntry.configure(state="normal")
        configEntry.delete(0, END)
        configEntry.insert(0, file_path)
        configEntry.configure(state="readonly")

    def saveConfig():
        with open(STATE.config_path.get(), "w+") as config:
            config.write(STATE.config.get())

    def updateTemplatePath(*args):
        nonlocal templatePath
        with resources.path(mech, "templates") as path:
            templatePath = os.path.join(path, STATE.project_type.get())
        getDefaultConfig()

    def updateConfigPath(*args):
        configEntry.configure(state="normal")
        STATE.config_path.set(os.path.join(STATE.project_path.get(), "robotconfig.py"))
        configEntry.configure(state="readonly")

    def getDefaultConfig():
        with open(os.path.join(templatePath, "robotconfig.py"), "r") as config:
            STATE.config.set(config.read())

    def readConfig():
        try:
            with open(STATE.config_path.get(), "r") as config:
                STATE.config.set(config.read())
        except:
            tkinter.messagebox.showerror("Error!", "Could not open/read config file.")
            return

    def genProject():
        dst = os.path.join(STATE.project_path.get(), "characterization-project")
        try:
            with resources.path(res, "project") as path:
                shutil.copytree(
                    src=path,
                    dst=dst,
                )
                with open(
                    os.path.join(dst, "src", "main", "java", "dc", "Robot.java"), "w+"
                ) as robot:
                    robot.write(
                        mech.genRobotCode(
                            STATE.project_type.get(), eval(STATE.config.get())
                        )
                    )
                with open(os.path.join(dst, "Build.gradle"), "w+") as build:
                    build.write(
                        mech.genBuildGradle(
                            STATE.project_type.get(), STATE.team_number.get()
                        )
                    )
        except FileExistsError:
            if tkinter.messagebox.askyesno(
                "Warning!",
                "Project directory already exists!  Do you want to overwrite it?",
            ):
                shutil.rmtree(dst)
                genProject()
        except Exception as e:
            tkinter.messagebox.showerror(
                "Error!",
                "Unable to generate project - config may be bad.\n"
                + 'Details:\n'
                + repr(e),
            )
            shutil.rmtree(dst)

    def deployProject():
        if STATE.team_number.get() == 0:
            cmd = "simulatejava"
        else:
            cmd = "deploy"

        if os.name == "nt":
            try:
                process = Popen(
                    [
                        os.path.join(
                            STATE.project_path.get(),
                            "characterization-project",
                            "gradlew.bat",
                        ),
                        cmd,
                        "--console=plain",
                    ],
                    stdout=PIPE,
                    stderr=STDOUT,
                    cwd=os.path.join(STATE.project_path.get(), "characterization-project"),
                )
            except Exception as e:
                tkinter.messagebox.showerror('Error!', 'Could not call gradlew deploy.\n' + 'Details:\n' + repr(e))
                return
        else:
            try:
                process = Popen(
                    [
                        os.path.join(
                            STATE.project_path.get(), "characterization-project", "gradlew"
                        ),
                        cmd,
                        "--console=plain",
                    ],
                    stdout=PIPE,
                    stderr=STDOUT,
                    cwd=os.path.join(STATE.project_path.get(), "characterization-project"),
                )
            except Exception as e:
                tkinter.messagebox.showerror('Error!', 'Could not call gradlew deploy.\n' + 'Details:\n' + repr(e))
                return

        window = stdoutWindow()
        STATE.mainGUI.after(10, lambda: updateStdout(process, window))

    class stdoutWindow(tkinter.Toplevel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title("Deploy Progress")

            self.stdoutText = ScrolledText(self, width=60, height=15)
            self.stdoutText.grid(row=0, column=0)

    def updateStdout(process, window):
        if window.winfo_exists():
            out = process.stdout.readline()
            if out != "":
                window.stdoutText.insert(END, out)

            if process.poll() is None:
                STATE.mainGUI.after(10, lambda: updateStdout(process, window))
            elif process.poll() != 0:
                tkinter.messagebox.showerror(
                    "Error!",
                    "Deployment failed!\n" + "Check the console for more details.",
                    parent=window
                )

    def runLogger():
        mech.data_logger.main(STATE.team_number.get(), STATE.project_path.get())

    def runAnalyzer():
        mech.data_analyzer.main(STATE.project_path.get())

    templatePath = None
    updateTemplatePath()

    getDefaultConfig()

    # TOP OF WINDOW

    topFrame = Frame(STATE.mainGUI)
    topFrame.grid(row=0, column=0, sticky="ew")

    Button(topFrame, text="Select Project Location", command=getProjectLocation).grid(
        row=0, column=0, sticky="ew"
    )

    projLocationEntry = Entry(
        topFrame, textvariable=STATE.project_path, width=80, state="readonly"
    )
    projLocationEntry.grid(row=0, column=1, columnspan=10)
    STATE.project_path.trace_add("write", updateConfigPath)

    Label(topFrame, text="Project Type:", anchor="e").grid(
        row=0, column=11, sticky="ew"
    )

    projectChoices = {"Simple", "Talon"}
    projTypeMenu = OptionMenu(topFrame, STATE.project_type, *sorted(projectChoices))
    projTypeMenu.configure(width=10)
    projTypeMenu.grid(row=0, column=12, sticky="ew")
    STATE.project_type.trace_add("write", updateTemplatePath)

    Button(topFrame, text="Select Config File", command=getConfigPath).grid(
        row=1, column=0, sticky="ew"
    )
    configEntry = Entry(
        topFrame, textvariable=STATE.config_path, width=80, state="readonly"
    )
    configEntry.grid(row=1, column=1, columnspan=10)

    Button(topFrame, text="Save Config", command=saveConfig).grid(row=1, column=11)

    readConfigButton = Button(topFrame, text="Read Config", command=readConfig)
    readConfigButton.grid(row=1, column=12, sticky="ew")

    Label(topFrame, text="Team Number:", anchor="e").grid(row=2, column=0, sticky="ew")
    teamNumberEntry = IntEntry(topFrame, textvariable=STATE.team_number)
    teamNumberEntry.grid(row=2, column=1, sticky="ew")

    for child in topFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    # Body Frame

    bodyFrame = Frame(STATE.mainGUI, bd=2, relief="groove")
    bodyFrame.grid(row=1, column=0, sticky="ew")

    genProjButton = Button(bodyFrame, text="Generate Project", command=genProject)
    genProjButton.grid(row=1, column=0, sticky="ew")

    deployButton = Button(bodyFrame, text="Deploy Project", command=deployProject)
    deployButton.grid(row=2, column=0, sticky="ew")

    loggerButton = Button(bodyFrame, text="Launch Data Logger", command=runLogger)
    loggerButton.grid(row=3, column=0, sticky="ew")

    analyzerButton = Button(bodyFrame, text="Launch Data Analyzer", command=runAnalyzer)
    analyzerButton.grid(row=4, column=0, sticky="ew")

    configEditPane = TextExtension(bodyFrame, textvariable=STATE.config)
    configEditPane.grid(row=0, column=1, rowspan=30, columnspan=10)

    for child in bodyFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)


class GuiState:
    def __init__(self):
        self.mainGUI = tkinter.Tk()

        self.project_path = StringVar(self.mainGUI)
        self.project_path.set(os.getcwd())

        self.config_path = StringVar(self.mainGUI)
        self.config_path.set(os.path.join(os.getcwd(), "robotconfig.py"))

        self.project_type = StringVar(self.mainGUI)
        self.project_type.set("Simple")

        self.config = StringVar(self.mainGUI)

        self.team_number = IntVar(self.mainGUI)


def main(mech):
    STATE = GuiState()

    configureGUI(STATE, mech)
    STATE.mainGUI.title("RobotPy Characterization New Project Tool")

    STATE.mainGUI.mainloop()


if __name__ == "__main__":

    main(drive_characterization)
