# The GUI for running the data logger for each project.  As the GUI does not vary by project,
# the logger runner is simply injected into this GUI.

import json
import os
import queue
import threading
import time
import tkinter
from tkinter import *
import logging

from networktables import NetworkTables
from frc_characterization.newproject import Tests, Units
from frc_characterization.utils import FloatEntry, IntEntry

# GUI SETUP

logger = logging.getLogger("logger")
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)


class Test:
    def __init__(
        self, button_text, on_click, status_text_val, option_label=None, option_val=None
    ):
        self._button_text = button_text
        self._on_click = on_click
        self._status_text_val = status_text_val
        self._option_label = option_label
        self._option_val = option_val

        self._run_button = None
        self._status_entry = None

    def addToGUI(self, frame, row, disable_all_buttons, mainGUI):
        self._run_button = Button(
            frame,
            text=self._button_text,
            command=lambda: (
                disable_all_buttons(),
                self._status_text_val.set("Running..."),
                self._on_click(),
            ),
            state="disabled",
        )
        self._run_button.grid(row=row, column=0, sticky="ew")

        status = Entry(frame, textvariable=self._status_text_val)
        status.configure(state="readonly")
        status.grid(row=row, column=1)

        if self._option_label != None and self._option_val != None:
            Label(frame, text=self._option_label, anchor="e").grid(
                row=row, column=2, sticky="ew"
            )

            FloatEntry(frame, textvariable=self._option_val).grid(
                row=row, column=3, sticky="ew"
            )

    def disable(self):
        if self._run_button != None:
            self._run_button.configure(state="disabled")

    def enable(self):
        if self._run_button != None:
            self._run_button.configure(state="normal")

    def isCompleted(self):
        return self._status_text_val.get() == "Completed"

    def getName(self):
        return self._button_text


def configure_gui(STATE, RUNNER):
    tests = []

    def getFile():
        file_path = tkinter.filedialog.asksaveasfilename(
            parent=STATE.mainGUI,
            title="Choose the data file (.JSON)",
            initialdir=os.getcwd(),
            defaultextension=".json",
            filetypes=(("JSON", "*.json"),),
        )
        fileEntry.configure(state="normal")
        fileEntry.delete(0, END)
        fileEntry.insert(0, file_path)
        fileEntry.configure(state="readonly")

    def save():
        if STATE.timestamp_enabled.get():
            name, ext = os.path.splitext(STATE.file_path.get())
            filename = name + time.strftime("%Y%m%d-%H%M") + ext
        with open(filename, "w") as fp:
            data = RUNNER.stored_data
            data.update({"test": STATE.test.get()})
            data.update({"units": STATE.units.get()})
            data.update({"unitsPerRotation": STATE.units_per_rot.get()})
            json.dump(data, fp, indent=4, separators=(",", ": "))

    def connect():
        if STATE.connect_handle:
            STATE.mainGUI.after_cancel(STATE.connect_handle)

        if STATE.team_number.get() != 0:
            NetworkTables.startClientTeam(STATE.team_number.get())
        else:
            NetworkTables.initialize(server="localhost")

        NetworkTables.addConnectionListener(
            RUNNER.connectionListener, immediateNotify=True
        )
        NetworkTables.addEntryListener(RUNNER.valueChanged)

        STATE.connected.set("Connecting...")

        waitForConnection()

    def waitForConnection():
        if RUNNER.get_nowait() == "connected":
            STATE.connected.set("Connected")
            enableTestButtons()
            changeTests()
            testTypeMenu.configure(state="normal")
        else:
            STATE.connect_handle = STATE.mainGUI.after(10, waitForConnection)

    def disableTestButtons():
        for step in tests:
            step.disable()
        saveButton.configure(state="disabled")

    def enableTestButtons():
        all_completed = True
        for step in tests:
            # Don't have to do trackwidth if not drivetrain
            if step.getName() != "Trackwidth":
                step.enable()
                all_completed &= step.isCompleted()
            else:
                if STATE.test.get() == "Drivetrain":
                    step.enable()
                    all_completed &= step.isCompleted()

        if all_completed:
            saveButton.configure(state="normal")

    def finishTest(textEntry):
        textEntry.set("Completed")
        enableTestButtons()

    def runPostedTasks():
        while STATE.runTask():
            pass
        STATE.task_handle = STATE.mainGUI.after(10, runPostedTasks)

    def quasiForward():
        threading.Thread(
            target=RUNNER.runTest,
            args=(
                "slow-forward",
                0,
                STATE.quasi_ramp_rate.get(),
                lambda: finishTest(STATE.sf_completed),
            ),
        ).start()

    def quasiBackward():
        threading.Thread(
            target=RUNNER.runTest,
            args=(
                "slow-backward",
                0,
                -STATE.quasi_ramp_rate.get(),
                lambda: finishTest(STATE.sb_completed),
            ),
        ).start()

    def dynamicForward():
        threading.Thread(
            target=RUNNER.runTest,
            args=(
                "fast-forward",
                STATE.dynamic_step_voltage.get(),
                0,
                lambda: finishTest(STATE.ff_completed),
            ),
        ).start()

    def dynamicBackward():
        threading.Thread(
            target=RUNNER.runTest,
            args=(
                "fast-backward",
                -STATE.dynamic_step_voltage.get(),
                0,
                lambda: finishTest(STATE.fb_completed),
            ),
        ).start()

    def trackWidth():
        threading.Thread(
            target=RUNNER.runTest,
            args=(
                "track-width",
                STATE.rotation_voltage.get(),
                0,
                lambda: (STATE.trw_completed.set("Completed"), enableTestButtons()),
                True,
            ),
        ).start()

    def changeTests(*args):
        # disable/enable trackwidth test
        if tests:
            track_width_index = 0
            for i in range(len(tests)):
                if tests[i].getName() == "Trackwidth":
                    track_width_index = i
                    break
            track_width = tests[track_width_index]
            if STATE.test.get() != "Drivetrain":
                track_width.disable()
                angularEnabled.configure(state="disabled")
            else:
                track_width.enable()
                angularEnabled.configure(state="normal")

    # TOP OF WINDOW (FILE SELECTION)

    topFrame = Frame(STATE.mainGUI)
    topFrame.grid(row=0, column=0)

    Button(topFrame, text="Select Save Location/Name", command=getFile).grid(
        row=0, column=0, sticky="ew"
    )

    fileEntry = Entry(topFrame, textvariable=STATE.file_path, width=80)
    fileEntry.grid(row=0, column=1, columnspan=10)
    fileEntry.configure(state="readonly")

    saveButton = Button(topFrame, text="Save Data", command=save, state="disabled")
    saveButton.grid(row=1, column=0, sticky="ew")

    Label(topFrame, text="Add Timestamp:", anchor="e").grid(
        row=1, column=1, sticky="ew"
    )
    timestampEnabled = Checkbutton(topFrame, variable=STATE.timestamp_enabled)
    timestampEnabled.grid(row=1, column=2)

    Label(topFrame, text="Test Type:", anchor="e").grid(row=1, column=3, sticky="ew")

    testTypeMenu = OptionMenu(
        topFrame, STATE.test, *sorted(test.value for test in Tests)
    )
    testTypeMenu.grid(row=1, column=4)
    testTypeMenu.configure(state="disabled")
    STATE.test.trace_add("write", changeTests)

    Label(topFrame, text="Angular Mode:", anchor="e").grid(row=2, column=3, sticky="ew")
    angularEnabled = Checkbutton(topFrame, variable=STATE.angular_mode)
    angularEnabled.grid(row=2, column=4)
    angularEnabled.configure(state="disabled")

    for child in topFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    STATE.topFrame = topFrame

    # WINDOW BODY (TEST RUNNING CONTROLS)

    bodyFrame = Frame(STATE.mainGUI, bd=2, relief="groove")
    bodyFrame.grid(row=1, column=0, sticky="ew")

    connectButton = Button(bodyFrame, text="Connect to Robot", command=connect)
    connectButton.grid(row=0, column=0, sticky="ew")

    connected = Entry(bodyFrame, textvariable=STATE.connected)
    connected.configure(state="readonly")
    connected.grid(row=0, column=1, sticky="ew")

    Label(bodyFrame, text="Team Number:", anchor="e").grid(row=0, column=2, sticky="ew")
    teamNumEntry = IntEntry(bodyFrame, textvariable=STATE.team_number, width=6)
    teamNumEntry.grid(row=0, column=3, sticky="ew")

    tests = [
        Test(
            "Quasistatic Forward",
            quasiForward,
            STATE.sf_completed,
            "Quasistatic ramp rate (V/s):",
            STATE.quasi_ramp_rate,
        ),
        Test("Quasistatic Backward", quasiBackward, STATE.sb_completed),
        Test(
            "Dynamic Forward",
            dynamicForward,
            STATE.ff_completed,
            "Dynamic step voltage (V):",
            STATE.dynamic_step_voltage,
        ),
        Test("Dynamic Backward", dynamicBackward, STATE.fb_completed),
        Test(
            "Trackwidth",
            trackWidth,
            STATE.trw_completed,
            "Rotation Wheel voltage (V):",
            STATE.rotation_voltage,
        ),
    ]

    for row, step in enumerate(tests, start=1):
        step.addToGUI(bodyFrame, row, disableTestButtons, STATE.mainGUI)

    for child in bodyFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    runPostedTasks()


class GuiState:
    def __init__(
        self,
        team,
        dir,
        unit=Units.ROTATIONS,
        units_per_rot=1,
        test=Tests.SIMPLE_MOTOR,
    ):
        self.mainGUI = tkinter.Tk()

        self.file_path = StringVar(self.mainGUI)
        self.file_path.set(os.path.join(dir, "characterization-data.json"))

        self.timestamp_enabled = BooleanVar(self.mainGUI)
        self.timestamp_enabled.set(True)

        self.team_number = IntVar(self.mainGUI)
        self.team_number.set(team)

        self.connected = StringVar(self.mainGUI)
        self.connected.set("Not connected")

        self.sf_completed = StringVar(self.mainGUI)
        self.sf_completed.set("Not Run")

        self.sb_completed = StringVar(self.mainGUI)
        self.sb_completed.set("Not Run")

        self.ff_completed = StringVar(self.mainGUI)
        self.ff_completed.set("Not Run")

        self.fb_completed = StringVar(self.mainGUI)
        self.fb_completed.set("Not Run")

        self.quasi_ramp_rate = DoubleVar(self.mainGUI)
        self.quasi_ramp_rate.set(0.25)

        self.dynamic_step_voltage = DoubleVar(self.mainGUI)
        self.dynamic_step_voltage.set(6)

        self.task_queue = queue.Queue()

        self.task_handle = None
        self.connect_handle = None

        self.test = StringVar(self.mainGUI)
        self.test.set(test.value)

        self.angular_mode = BooleanVar(self.mainGUI)
        self.angular_mode.set(False)

        self.units = StringVar(self.mainGUI)
        self.units.set(unit.value)

        self.units_per_rot = DoubleVar(self.mainGUI)
        self.units_per_rot.set(units_per_rot)

        def onClose():
            self.mainGUI.after_cancel(self.task_handle)
            self.mainGUI.destroy()

        self.mainGUI.protocol("WM_DELETE_WINDOW", onClose)

    def postTask(self, task):
        self.task_queue.put(task)

    def runTask(self):
        try:
            self.task_queue.get_nowait()()
            return True
        except queue.Empty:
            return False


def main(
    team,
    dir,
    runner,
    unit=Units.ROTATIONS,
    units_per_rot=1,
    test=Tests.SIMPLE_MOTOR,
):

    STATE = GuiState(team, dir, unit, units_per_rot, test)
    RUNNER = runner(STATE)

    STATE.mainGUI.title("FRC Characterization Data Logger")

    configure_gui(STATE, RUNNER)

    STATE.mainGUI.mainloop()


if __name__ == "__main__":
    from frc_characterization.logger_analyzer.data_logger import TestRunner

    main(0, os.getcwd(), TestRunner)
