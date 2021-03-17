# The "new project" GUI - this serves as the "home window" from which an entire
# characterization project can be run.
#
# Offers in-window editing of config files for robot-side code generation.
#
# Note that the project-specific python package is injected - this is a slightly
# odd pattern, but allows none of this code to be duplicated so long as the
# individual project packages all have the same structure.

import os
import pathlib
import shutil
import tkinter
import threading
import time
import glob
import zipfile
from datetime import datetime
from enum import Enum
from importlib import import_module
from subprocess import PIPE, Popen, STDOUT
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import logging
import math
import queue

import frc_characterization
from frc_characterization.utils import IntEntry, TextExtension, FloatEntry
import frc_characterization.robot as res

import pint

logger = logging.getLogger("logger")
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"


class Tests(Enum):
    ARM = "Arm"
    ELEVATOR = "Elevator"
    DRIVETRAIN = "Drivetrain"
    SIMPLE_MOTOR = "Simple"


class Units(Enum):
    __ureg__ = pint.UnitRegistry()

    FEET = "Feet", __ureg__.foot
    METERS = "Meters", __ureg__.meter
    INCHES = "Inches", __ureg__.inch
    RADIANS = "Radians", __ureg__.radian
    DEGREES = "Degrees", __ureg__.degree
    ROTATIONS = "Rotations", __ureg__.revolution

    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]

        # ureg value
        obj.unit = values[1]
        return obj


class NewProjectGUI:
    def __init__(self, testType):
        self.mainGUI = tkinter.Tk()

        self.project_path = StringVar(self.mainGUI)
        self.project_path.set(os.getcwd())

        self.config_path = StringVar(self.mainGUI)
        self.config_path.set(os.path.join(os.getcwd(), "robotconfig.py"))

        self.project_type = StringVar(self.mainGUI)
        self.project_type.set(testType.value)

        self.config = StringVar(self.mainGUI)

        self.team_number = IntVar(self.mainGUI)

        self.units = StringVar(self.mainGUI)
        self.units.set(Units.ROTATIONS.value)

        self.units_per_rot = DoubleVar(self.mainGUI)
        self.units_per_rot.set(1)

        self.control_type = StringVar(self.mainGUI)
        self.control_type.set("Simple")

    def configureGUI(self):
        mech = frc_characterization.logger_analyzer

        def getProjectLocation():
            file_path = filedialog.askdirectory(
                title="Choose the project location", initialdir=self.project_path.get()
            )
            projLocationEntry.configure(state="normal")
            projLocationEntry.delete(0, END)
            projLocationEntry.insert(0, file_path)
            projLocationEntry.configure(state="readonly")

        def getConfigPath():
            file_path = tkinter.filedialog.askopenfilename(
                title="Choose the config file",
                initialdir=self.project_path.get(),
                filetypes=(("Python", "*.py"),),
            )
            configEntry.configure(state="normal")
            configEntry.delete(0, END)
            configEntry.insert(0, file_path)
            configEntry.configure(state="readonly")

        def saveConfig():
            with open(self.config_path.get(), "w+") as config:
                config.write(self.config.get())

        # TODO: Replace with Python 3.9's resources.files() when it becomes min version
        def files(package):
            if hasattr(package, "__spec__"):
                spec = package.__spec__
            else:
                spec = import_module(package).__spec__
            if spec.submodule_search_locations is None:
                raise TypeError("{!r} is not a package".format(package))

            package_directory = pathlib.Path(spec.origin).parent
            try:
                archive_path = spec.loader.archive
                rel_path = package_directory.relative_to(archive_path)
                return zipfile.Path(archive_path, str(rel_path) + "/")
            except Exception:
                pass
            return package_directory

        def updateTemplatePath(*args):
            nonlocal templatePath
            templatePath = files(mech).joinpath("templates")
            getDefaultConfig()

        def updateConfigPath(*args):
            configEntry.configure(state="normal")
            self.config_path.set(
                os.path.join(self.project_path.get(), "robotconfig.py")
            )
            configEntry.configure(state="readonly")

        def getDefaultConfig(*args):
            with open(
                os.path.join(
                    templatePath, f"configs/{self.control_type.get().lower()}config.py"
                ),
                "r",
            ) as config:
                self.config.set(config.read())

        def readConfig():
            try:
                with open(self.config_path.get(), "r") as config:
                    self.config.set(config.read())
            except:
                messagebox.showerror("Error!", "Could not open/read config file.")
                return

        def genProject():
            config = eval(
                compile(self.config.get(), self.config_path.get(), "eval"),
                {"__builtins__": {}},
            )
            config["controlType"] = self.control_type.get()
            if self.control_type.get() == "SparkMax":
                config["controllerTypes"] = ["CANSparkMax"]
                config["rightControllerTypes"] = ["CANSparkMax"]
            logger.info(f"Config: {config}")
            dst = os.path.join(self.project_path.get(), "characterization-project")
            try:
                path = files(res).joinpath("project")
                shutil.copytree(src=path, dst=dst)
                with open(
                    os.path.join(dst, "src", "main", "java", "dc", "Robot.java"),
                    "w+",
                ) as robot:
                    robot.write(mech.gen_robot_code(config))
                with open(os.path.join(dst, "build.gradle"), "w+") as build:
                    build.write(
                        mech.gen_build_gradle(
                            self.team_number.get(),
                        )
                    )
            except FileExistsError:
                if messagebox.askyesno(
                    "Warning!",
                    "Project directory already exists!  Do you want to overwrite it?",
                ):
                    shutil.rmtree(dst)
                    genProject()
            except Exception as e:
                messagebox.showerror(
                    "Error!",
                    "Unable to generate project - config may be bad.\n"
                    + "Details:\n"
                    + repr(e),
                )
                shutil.rmtree(dst)

        def deployProject(queue):
            if self.team_number.get() == 0:
                cmd = "simulatejava"
            else:
                cmd = "deploy"

            def append_latest_jdk(process_args, jdk_base_path):
                possible_jdk_paths = glob.glob(
                    os.path.join(jdk_base_path, "20[0-9][0-9]")
                )

                if len(possible_jdk_paths) <= 0:
                    queue.put(
                        (
                            "Warning!",
                            "You not appear to have any wpilib JDK installed. If your system JDK is the wrong version then the deploy will fail.",
                        )
                    )
                    return

                year = max([int(os.path.basename(path)) for path in possible_jdk_paths])
                process_args.append(
                    "-Dorg.gradle.java.home="
                    + os.path.join(jdk_base_path, str(year), "jdk")
                )

                if int(year) != datetime.now().year:
                    queue.put(
                        (
                            "Warning!",
                            f"Your latest wpilib JDK's year ({year}) doesn't match the current year ({datetime.now().year}). Your deploy may fail.",
                        )
                    )

            if os.name == "nt":
                process_args = [
                    os.path.join(
                        self.project_path.get(),
                        "characterization-project",
                        "gradlew.bat",
                    ),
                    cmd,
                    "--console=plain",
                ]

                # C:/Users/Public/wpilib/YEAR/jdk is correct *as of* wpilib 2020
                # Prior to 2020 the path was C:/Users/Public/frcYEAR/jdk
                jdk_base_path = os.path.join(
                    os.path.abspath(os.path.join(os.path.expanduser("~"), "..")),
                    "Public",
                    "wpilib",
                )
                append_latest_jdk(process_args, jdk_base_path)

                try:
                    process = Popen(
                        process_args,
                        stdout=PIPE,
                        stderr=STDOUT,
                        cwd=os.path.join(
                            self.project_path.get(), "characterization-project"
                        ),
                    )
                except Exception as e:
                    queue.put(
                        (
                            "Error!",
                            "Could not call gradlew deploy.\n" + "Details:\n" + repr(e),
                        )
                    )
                    return
            else:
                process_args = [
                    os.path.join(
                        self.project_path.get(), "characterization-project", "gradlew"
                    ),
                    cmd,
                    "--console=plain",
                ]

                # This path is correct *as of* wpilib 2020
                # Prior to 2020 the path was ~/frcYEAR/jdk
                jdk_base_path = os.path.join(os.path.expanduser("~"), "wpilib")
                append_latest_jdk(process_args, jdk_base_path)

                try:
                    process = Popen(
                        process_args,
                        stdout=PIPE,
                        stderr=STDOUT,
                        cwd=os.path.join(
                            self.project_path.get(), "characterization-project"
                        ),
                    )
                except Exception as e:
                    queue.put(
                        (
                            "Error!",
                            "Could not call gradlew deploy.\n" + "Details:\n" + repr(e),
                        )
                    )
                    return

            while process.poll() is None:
                time.sleep(0.1)
                queue.put(("Console", process.stdout.readline()))

            if process.poll() != 0:
                queue.put(
                    (
                        "Error!",
                        "Deployment failed!\n" + "Check the console for more details.",
                    )
                )

            # finish adding any outputs
            out = process.stdout.readline()
            while out:
                queue.put(("Console", out))
                out = process.stdout.readline()

        def processError(message):
            if "Warning!" == message[0]:
                messagebox.showwarning(
                    message[0], message[1], parent=self.deploy_window
                )
            else:
                messagebox.showerror(message[0], message[1], parent=self.deploy_window)

        def threadedDeploy():
            logger.info("Starting Deploy")
            self.queue = queue.Queue()
            self.deploy_window = stdoutWindow()

            ThreadedTask(self.queue).start()
            self.mainGUI.after(10, processQueue)

        def processQueue():
            try:
                msg = self.queue.get_nowait()
                if msg != "Task Finished":
                    if msg[0] != "Console":
                        processError(msg)
                    else:
                        updateStdout(msg[1])

                    self.mainGUI.after(10, processQueue)
            except queue.Empty:
                self.mainGUI.after(10, processQueue)

        class ThreadedTask(threading.Thread):
            def __init__(self, queue):
                threading.Thread.__init__(self)
                self.queue = queue

            def run(self):
                deployProject(self.queue)
                self.queue.put("Task Finished")
                logger.info("Finished Deploy")

        class stdoutWindow(tkinter.Toplevel):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.title("Deploy Progress")

                self.stdoutText = ScrolledText(self, width=60, height=15)
                self.stdoutText.grid(row=0, column=0)

        def updateStdout(out):
            if self.deploy_window.winfo_exists():
                if out != "":
                    self.deploy_window.stdoutText.insert(END, out)

        def runLogger():
            mech.data_logger.main(
                self.team_number.get(),
                self.project_path.get(),
                units=Units(self.units.get()),
                units_per_rot=self.units_per_rot.get(),
                test=Tests(self.project_type.get()),
            )

        def runAnalyzer():
            mech.data_analyzer.main(self.project_path.get())

        def enableUnitPerRot(*args):
            units = self.units.get()
            if isRotation(units):
                ureg = pint.UnitRegistry()
                units = Units(units)
                unitsRotationEntry.configure(state="readonly")
                self.units_per_rot.set(
                    round((1 * ureg.revolution).to(units.unit).magnitude, 3)
                )
            else:
                self.units_per_rot.set(0)
                unitsRotationEntry.configure(state="normal")

        def isRotation(units):
            return Units(units) in (Units.ROTATIONS, Units.RADIANS, Units.DEGREES)

        templatePath = None
        updateTemplatePath()

        getDefaultConfig()

        # TOP OF WINDOW

        topFrame = Frame(self.mainGUI)
        topFrame.grid(row=0, column=0, sticky="ew")

        Button(
            topFrame, text="Select Project Location", command=getProjectLocation
        ).grid(row=0, column=0, sticky="ew")

        projLocationEntry = Entry(
            topFrame, textvariable=self.project_path, width=80, state="readonly"
        )
        projLocationEntry.grid(row=0, column=1, columnspan=10)
        self.project_path.trace_add("write", updateConfigPath)

        Label(topFrame, text="Project Type:", anchor="e").grid(
            row=0, column=11, sticky="ew"
        )

        projTypeMenu = OptionMenu(
            topFrame, self.project_type, *sorted(test.value for test in Tests)
        )
        projTypeMenu.configure(width=25)
        projTypeMenu.grid(row=0, column=12, sticky="ew")

        Button(topFrame, text="Select Config File", command=getConfigPath).grid(
            row=1, column=0, sticky="ew"
        )
        configEntry = Entry(
            topFrame, textvariable=self.config_path, width=80, state="readonly"
        )
        configEntry.grid(row=1, column=1, columnspan=10)

        Button(topFrame, text="Save Config", command=saveConfig).grid(row=1, column=11)

        readConfigButton = Button(topFrame, text="Read Config", command=readConfig)
        readConfigButton.grid(row=1, column=12, sticky="ew")

        Label(topFrame, text="Team Number:", anchor="e").grid(
            row=2, column=0, sticky="ew"
        )
        teamNumberEntry = IntEntry(topFrame, textvariable=self.team_number)
        teamNumberEntry.grid(row=2, column=1, sticky="ew")

        Label(topFrame, text="Unit Type:", anchor="e").grid(
            row=2, column=2, sticky="ew"
        )

        unitMenu = OptionMenu(
            topFrame, self.units, *sorted(unit.value for unit in Units)
        )
        unitMenu.configure(width=25)
        unitMenu.grid(row=2, column=3, sticky="ew")
        self.units.trace_add("write", enableUnitPerRot)

        Label(topFrame, text="Units per Rotation:", anchor="e").grid(
            row=2, column=4, sticky="ew"
        )
        unitsRotationEntry = FloatEntry(topFrame, textvariable=self.units_per_rot)
        unitsRotationEntry.grid(row=2, column=5, sticky="ew")
        unitsRotationEntry.configure(state="readonly")

        Label(topFrame, text="Control Type:", anchor="e").grid(
            row=2, column=11, sticky="ew"
        )

        controlMenu = OptionMenu(
            topFrame, self.control_type, *["Simple", "CTRE", "SparkMax", "Venom"]
        )
        controlMenu.configure(width=25)
        controlMenu.grid(row=2, column=12, sticky="ew")
        self.control_type.trace_add("write", getDefaultConfig)

        for child in topFrame.winfo_children():
            child.grid_configure(padx=1, pady=1)

        # Body Frame

        bodyFrame = Frame(self.mainGUI, bd=2, relief="groove")
        bodyFrame.grid(row=1, column=0, sticky="ew")

        genProjButton = Button(bodyFrame, text="Generate Project", command=genProject)
        genProjButton.grid(row=1, column=0, sticky="ew")

        deployButton = Button(bodyFrame, text="Deploy Project", command=threadedDeploy)
        deployButton.grid(row=2, column=0, sticky="ew")

        loggerButton = Button(bodyFrame, text="Launch Data Logger", command=runLogger)
        loggerButton.grid(row=3, column=0, sticky="ew")

        analyzerButton = Button(
            bodyFrame, text="Launch Data Analyzer", command=runAnalyzer
        )
        analyzerButton.grid(row=4, column=0, sticky="ew")

        configEditPane = TextExtension(bodyFrame, textvariable=self.config)
        configEditPane.grid(row=0, column=1, rowspan=30, columnspan=10)

        for child in bodyFrame.winfo_children():
            child.grid_configure(padx=1, pady=1)


def main(testType):
    project = NewProjectGUI(testType)

    project.configureGUI()
    project.mainGUI.title("FRC Characterization New Project Tool")

    project.mainGUI.mainloop()


if __name__ == "__main__":

    main(Tests.DRIVETRAIN)
