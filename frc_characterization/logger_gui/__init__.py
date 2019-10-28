# The GUI for running the data logger for each project.  As the GUI does not vary by project,
# the logger runner is simply injected into this GUI.

import json
import os
import queue
import threading
import time
import tkinter
from tkinter import *

from networktables import NetworkTables
from frc_characterization.utils import FloatEntry, IntEntry

# GUI SETUP


def configure_gui(STATE, RUNNER):
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
            json.dump(RUNNER.stored_data, fp, indent=4, separators=(",", ": "))

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
        else:
            STATE.connect_handle = STATE.mainGUI.after(10, waitForConnection)

    def disableTestButtons():
        quasiForwardButton.configure(state="disabled")
        quasiBackwardButton.configure(state="disabled")
        dynamicForwardButton.configure(state="disabled")
        dynamicBackwardButton.configure(state="disabled")
        saveButton.configure(state="disabled")

    def enableTestButtons():
        quasiForwardButton.configure(state="normal")
        quasiBackwardButton.configure(state="normal")
        dynamicForwardButton.configure(state="normal")
        dynamicBackwardButton.configure(state="normal")
        if (
            STATE.sf_completed.get() == "Completed"
            and STATE.sb_completed.get() == "Completed"
            and STATE.ff_completed.get() == "Completed"
            and STATE.fb_completed.get() == "Completed"
        ):
            saveButton.configure(state="normal")

    def finishTest(textEntry):
        textEntry.set("Completed")
        enableTestButtons()

    def runPostedTasks():
        while STATE.runTask():
            pass
        STATE.task_handle = STATE.mainGUI.after(10, runPostedTasks)

    def quasiForward():
        disableTestButtons()
        STATE.sf_completed.set("Running...")
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
        disableTestButtons()
        STATE.sb_completed.set("Running...")
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
        disableTestButtons()
        STATE.ff_completed.set("Running...")
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
        disableTestButtons()
        STATE.fb_completed.set("Running...")
        threading.Thread(
            target=RUNNER.runTest,
            args=(
                "fast-backward",
                -STATE.dynamic_step_voltage.get(),
                0,
                lambda: finishTest(STATE.fb_completed),
            ),
        ).start()

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

    for child in topFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

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

    Label(bodyFrame, text="Quasistatic ramp rate (V/s):", anchor="e").grid(
        row=1, column=2, sticky="ew"
    )
    rampEntry = FloatEntry(bodyFrame, textvariable=STATE.quasi_ramp_rate)
    rampEntry.grid(row=1, column=3, sticky="ew")

    Label(bodyFrame, text="Dynamic step voltage (V):", anchor="e").grid(
        row=3, column=2, sticky="ew"
    )
    stepEntry = FloatEntry(bodyFrame, textvariable=STATE.dynamic_step_voltage)
    stepEntry.grid(row=3, column=3, sticky="ew")

    quasiForwardButton = Button(
        bodyFrame, text="Quasistatic Forward", command=quasiForward, state="disabled"
    )
    quasiForwardButton.grid(row=1, column=0, sticky="ew")

    quasiForwardCompleted = Entry(bodyFrame, textvariable=STATE.sf_completed)
    quasiForwardCompleted.configure(state="readonly")
    quasiForwardCompleted.grid(row=1, column=1)

    quasiBackwardButton = Button(
        bodyFrame, text="Quasistatic Backward", command=quasiBackward, state="disabled"
    )
    quasiBackwardButton.grid(row=2, column=0, sticky="ew")

    quasiBackwardCompleted = Entry(bodyFrame, textvariable=STATE.sb_completed)
    quasiBackwardCompleted.configure(state="readonly")
    quasiBackwardCompleted.grid(row=2, column=1)

    dynamicForwardButton = Button(
        bodyFrame, text="Dynamic Forward", command=dynamicForward, state="disabled"
    )
    dynamicForwardButton.grid(row=3, column=0, sticky="ew")

    dynamicForwardCompleted = Entry(bodyFrame, textvariable=STATE.ff_completed)
    dynamicForwardCompleted.configure(state="readonly")
    dynamicForwardCompleted.grid(row=3, column=1)

    dynamicBackwardButton = Button(
        bodyFrame, text="Dynamic Backward", command=dynamicBackward, state="disabled"
    )
    dynamicBackwardButton.grid(row=4, column=0, sticky="ew")

    dynamicBackwardCompleted = Entry(bodyFrame, textvariable=STATE.fb_completed)
    dynamicBackwardCompleted.configure(state="readonly")
    dynamicBackwardCompleted.grid(row=4, column=1)

    for child in bodyFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    runPostedTasks()

class GuiState:
    def __init__(self, team, dir):
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


def main(team, dir, runner):

    STATE = GuiState(team, dir)
    RUNNER = runner(STATE)

    STATE.mainGUI.title("FRC Characterization Data Logger")

    configure_gui(STATE, RUNNER)

    STATE.mainGUI.mainloop()


if __name__ == "__main__":
    from drive_characterization.data_logger import TestRunner

    main(0, os.getcwd(), TestRunner)

    # log_datefmt = '%H:%M:%S'
    # log_format = '%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s'

    # logging.basicConfig(level=logging.INFO, datefmt=log_datefmt, format=log_format)

    # dl = DataLogger()
    # dl.run()
