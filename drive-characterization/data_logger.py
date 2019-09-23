#!/usr/bin/env python3
#
# Adapted from the pynetworktables json_logger example program
#
# While this is designed to work with the robot.py example in this directory,
# because the transport uses NetworkTables you can use it with a robot program
# written in any FRC language.
#
# The expected NT interface is as follows:
#
# - /robot/autospeed : This program sends this to the robot. In autonomous mode,
#                      the robot should attempt to drive at this speed
#
# - /robot/telemetry : The robot sends this. It is a number array that contains:
#                      - time, battery, autospeed,
#                        lmotor_volts, rmotor_volts,
#                        l_encoder_count, r_encoder_count,
#                        l_encoder_velocity, r_encoder_velocity
#
# Change the following constant if your robot wheels are slipping during the
# the fast test, or if the robot is not moving
ROBOT_FAST_SPEED = 0.5


from networktables import NetworkTables, __version__ as ntversion
from networktables.util import ntproperty

# Older versions of pynetworktables (and ntcore) had bugs related to flush()
if tuple(map(int, ntversion.split(".")[:3])) < (2018, 1, 2):
    print("Requires pynetworktables >= 2018.1.3, %s is installed" % ntversion)
    exit(1)

import json
import queue
import time
import threading
import os

from data_analyzer import AUTOSPEED_COL, L_ENCODER_P_COL, R_ENCODER_P_COL

import tkinter
from tkinter import *

import logging

# GUI SETUP

mainGUI = tkinter.Tk()

STATE = None
RUNNER = None

def configure_gui():

    def getFile():
        file_path = tkinter.filedialog.asksaveasfilename(
            parent=mainGUI, title='Choose the data file (.JSON)', initialdir=os.getcwd(), defaultextension=".json", filetypes = (("JSON","*.json"),))
        fileEntry.configure(state='normal')
        fileEntry.delete(0, END)
        fileEntry.insert(0, file_path)
        fileEntry.configure(state='readonly')

    def save():
        if STATE.timestamp_enabled.get():
            name, ext = os.path.splitext(STATE.file_path.get())
            STATE.file_path.set(name + time.strftime("%Y%m%d-%H%M-%S") + ext)
        filename = filename + ".json"
        with open(filename, "w") as fp:
            json.dump(STATE.stored_data, fp, indent=4, separators=(",", ": "))

    def connect():
        if STATE.team_number.get():
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
            mainGUI.after(10, waitForConnection)

    def disableTestButtons():
            quasiForwardButton.configure(state='disabled')
            quasiBackwardButton.configure(state='disabled')
            dynamicForwardButton.configure(state='disabled')
            dynamicBackwardButton.configure(state='disabled')

    def enableTestButtons():
            quasiForwardButton.configure(state='normal')
            quasiBackwardButton.configure(state='normal')
            dynamicForwardButton.configure(state='normal')
            dynamicBackwardButton.configure(state='normal')

    def runPostedTasks():
        while STATE.runTask():
            pass
        mainGUI.after(10, runPostedTasks)

    def quasiForward():
        disableTestButtons()
        threading.Thread(target=RUNNER.runTest, args = ("slow-forward", 0, .001, enableTestButtons)).start()

    def quasiBackward():
        disableTestButtons()
        threading.Thread(target=RUNNER.runTest, args = ("slow-backward", 0, .001, enableTestButtons)).start()

    def dynamicForward():
        disableTestButtons()
        threading.Thread(target=RUNNER.runTest, args = ("fast-forward", 0, .001, enableTestButtons)).start()

    def dynamicBackward():
        disableTestButtons()
        threading.Thread(target=RUNNER.runTest, args = ("fast-backward", 0, .001, enableTestButtons)).start()


    # TOP OF WINDOW (FILE SELECTION)

    topFrame = Frame(mainGUI)
    topFrame.grid(row=0, column=0, columnspan=1)

    Button(topFrame, text="Select Save Location/Name",
           command=getFile).grid(row=0, column=0, padx=4)

    fileEntry = Entry(topFrame, textvariable=STATE.file_path, width=80)
    fileEntry.grid(row=0, column=1, columnspan=3)
    fileEntry.configure(state='readonly')

    Label(topFrame, text = "Add Timestamp:").grid(row=0, column=4)
    timestampEnabled = Checkbutton(topFrame, variable=STATE.timestamp_enabled)
    timestampEnabled.grid(row=0, column=5)

    saveButton = Button(topFrame, text="Save Data", command=save, state="disabled")
    saveButton.grid(row=0, column=6)

    Label(topFrame, text="Team Number:").grid(row=0, column=7)
    teamNumEntry = Entry(topFrame, textvariable=STATE.team_number, width=6)
    teamNumEntry.grid(row=0, column=8)

    # WINDOW BODY (TEST RUNNING CONTROLS)

    bodyFrame = Frame(mainGUI)
    bodyFrame.grid(row=1, column=0, columnspan=1)

    connectButton = Button(bodyFrame, text = "Connect to Robot", command = connect)
    connectButton.grid(row=0, column=0)

    Label(bodyFrame, text="Connected:").grid(row=0, column=1)

    connected = Entry(bodyFrame, textvariable=STATE.connected)
    connected.configure(state="readonly")
    connected.grid(row=0, column=2)

    quasiForwardButton = Button(bodyFrame, text = "Quasistatic Forward", command = quasiForward, state='disabled')
    quasiForwardButton.grid(row=1, column=0)

    quasiBackwardButton = Button(bodyFrame, text = "Quasistatic Backward", command = quasiBackward, state='disabled')
    quasiBackwardButton.grid(row=2, column=0)

    dynamicForwardButton = Button(bodyFrame, text = "Dynamic Backward", command = dynamicForward, state='disabled')
    dynamicForwardButton.grid(row=3, column=0)

    dynamicBackwardButton = Button(bodyFrame, text = "Dynamic Backward", command = dynamicBackward, state='disabled')
    dynamicBackwardButton.grid(row=4, column=0)

    runPostedTasks()

logger = logging.getLogger("logger")

# FMSControlData bitfields
ENABLED_FIELD = 1 << 0
AUTO_FIELD = 1 << 1
TEST_FIELD = 1 << 2
EMERGENCY_STOP_FIELD = 1 << 3
FMS_ATTACHED_FIELD = 1 << 4
DS_ATTACHED_FIELD = 1 << 5

def translate_control_word(value):
    value = int(value)
    if value & ENABLED_FIELD == 0:
        return "disabled"
    if value & AUTO_FIELD:
        return "auto"
    if value & TEST_FIELD:
        return "test"
    else:
        return "teleop"

class GuiState:

    # GUI bindings

    file_path = StringVar(mainGUI)
    timestamp_enabled = BooleanVar(mainGUI)
    team_number = IntVar(mainGUI)
    connected = StringVar(mainGUI)

    def __init__(self):
        # GUI bindings
        self.file_path.set(os.path.join(os.getcwd(), "characterization-data"))
        self.timestamp_enabled.set(True)
        self.team_number.set(0)
        self.connected.set("Not connected")

        self.task_queue = queue.Queue()

    def postTask(self, task):
        self.task_queue.put(task)

    def runTask(self):
        try:
            self.task_queue.get_nowait()()
            return True
        except queue.Empty:
            return False

class TestRunner:

    # Test data
    stored_data = None

    # Change this key to whatever NT key you want to log
    log_key = "/robot/telemetry"

    matchNumber = ntproperty("/FMSInfo/MatchNumber", 0, writeDefault=False)
    eventName = ntproperty("/FMSInfo/EventName", "unknown", writeDefault=False)

    autospeed = ntproperty("/robot/autospeed", 0, writeDefault=True)

    def __init__(self):

        self.stored_data = {}
        
        self.queue = queue.Queue()
        self.mode = "disabled"
        self.data = []
        self.lock = threading.Condition()

        # Tells the listener to not store data
        self.discard_data = True

        # Last telemetry data received from the robot
        self.last_data = (0,) * 20

    def connectionListener(self, connected, info):
        # set our robot to 'disabled' if the connection drops so that we can
        # guarantee the data gets written to disk
        if not connected:
            self.valueChanged("/FMSInfo/FMSControlData", 0, False)

        self.queue.put("connected" if connected else "disconnected")

    def valueChanged(self, key, value, isNew):

        if key == "/FMSInfo/FMSControlData":

            mode = translate_control_word(value)

            with self.lock:
                last = self.mode
                self.mode = mode

                data = self.data
                self.data = []

                self.lock.notifyAll()

            logger.info("Robot mode: %s -> %s", last, mode)

            # This example only stores on auto -> disabled transition. Change it
            # to whatever it is that you need for logging
            if last == "auto":
                logger.info("%d items received", len(data))

                # Don't block the NT thread -- write the data to the queue so
                # it can be processed elsewhere
                self.queue.put(data)

        elif key == self.log_key:

            self.last_data = value

            if not self.discard_data:
                with self.lock:
                    self.data.append(value)
                    dlen = len(self.data)

                if dlen and dlen % 100 == 0:
                    logger.info(
                        "Received %d datapoints (last commanded speed: %.2f)",
                        dlen,
                        value[AUTOSPEED_COL],
                    )

    def get_nowait(self, timeout=None):
        try:
            return self.queue.get(block=False, timeout=timeout)
        except queue.Empty:
            return queue.Empty

    def wait_for_stationary(self):
        # Wait for the velocity to be 0 for at least one second
        logger.info("Waiting for robot to stop moving for at least 1 second...")

        first_stationary_time = time.monotonic()
        last_l_encoder = 0
        last_r_encoder = 0

        while True:
            # check the queue in case we switched out of auto mode
            qdata = self.get_nowait()
            if qdata != queue.Empty:
                return qdata

            now = time.monotonic()

            # check the encoder position values, are they stationary?
            last_data = self.last_data

            try:
                l_encoder = last_data[L_ENCODER_P_COL]
                r_encoder = last_data[R_ENCODER_P_COL]
            except IndexError:
                print(self.last_data)
                raise

            if (
                abs(last_l_encoder - l_encoder) > 0.01
                or abs(last_r_encoder - r_encoder) > 0.01
            ):
                first_stationary_time = now
            elif now - first_stationary_time > 1:
                logger.info("Robot has waited long enough, beginning test")
                return

            last_l_encoder = l_encoder
            last_r_encoder = r_encoder

    def ramp_voltage_in_auto(self, initial_speed, ramp):

        logger.info(
            "Activating robot at %.1f%%, adding %.3f per 50ms", initial_speed, ramp
        )

        self.discard_data = False
        self.autospeed = initial_speed
        NetworkTables.flush()

        try:
            while True:
                # check the queue in case we switched out of auto mode
                qdata = self.get_nowait()
                if qdata != queue.Empty:
                    return qdata

                time.sleep(0.050)
                self.autospeed = self.autospeed + ramp

                NetworkTables.flush()
        finally:
            self.discard_data = True
            self.autospeed = 0

    def run(self):

        #
        # We have data! Do something with it now
        #
        # Write it to disk first, in case the processing fails for some reason
        # -> Using JSON for simplicity, maybe add csv at a later date

        now = time.strftime("%Y%m%d-%H%M-%S")
        fname = "%s-data.json" % now

        print()
        print("Data collection complete! saving to %s..." % fname)
        with open(fname, "w") as fp:
            json.dump(stored_data, fp, indent=4, separators=(",", ": "))

    def runTest(self, name, initial_speed, ramp, finished):
        try:
            # Initialize the robot commanded speed to 0
            self.autospeed = 0
            self.discard_data = True

            # print()
            # print(name)
            # print()
            # print("Please enable the robot in autonomous mode.")
            # print()
            # print(
            #     "WARNING: It will not automatically stop moving, so disable the robot"
            # )
            # print("before it hits something!")
            # print("")

            STATE.postTask(lambda: tkinter.messagebox.showinfo("Running " + name,
                                        "Please enable the robot in autonomous mode, and then "
                                        + "disable it before it runs out of space.\n"
                                        + "Note: The robot will continue to move until you disable it - "
                                        + "It is your responsibility to ensure it does not hit anything!"))

            # Wait for robot to signal that it entered autonomous mode
            with self.lock:
                self.lock.wait_for(lambda: self.mode == "auto")

            data = self.wait_for_stationary()
            if data is not None:
                if data in ("connected", "disconnected"):
                    STATE.postTask(lambda: tkinter.messagebox.showerror("Error!", "NT disconnected, results won't be reliable. Giving up."))
                    return
                else:
                    STATE.postTask(lambda: tkinter.messagebox.showerror("Error!", "Robot exited autonomous mode before data could be sent?"))
                    return

            # Ramp the voltage at the specified rate
            data = self.ramp_voltage_in_auto(initial_speed, ramp)
            if data in ("connected", "disconnected"):
                STATE.postTask(lambda: tkinter.messagebox.showerror("Error!", "NT disconnected, results won't be reliable. Giving up."))
                return

            # output sanity check
            if len(data) < 3:
               STATE.postTask(lambda: tkinter.messagebox.showwarning("Warning!", "There wasn't a lot of data received during that last run"))
            else:
                left_distance = data[-1][L_ENCODER_P_COL] - data[0][L_ENCODER_P_COL]
                right_distance = data[-1][R_ENCODER_P_COL] - data[0][R_ENCODER_P_COL]

                STATE.postTask(lambda: tkinter.messagebox.showmessage(name + " Complete",
                                               "The robot reported traveling the following distance:\n"
                                               + "Left:  %.3f ft" % left_distance + "\n"
                                               + "Right: %.3f ft" % right_distance + "\n"
                                               + "If that doesn't seem quite right... you should change the encoder calibration"
                                               + "in the robot program or fix your encoders!"))

            self.stored_data[name] = data
        
        finally:

            self.autospeed = 0

            STATE.postTask(finished)


def main():

    global STATE
    global RUNNER
    STATE = GuiState()
    RUNNER = TestRunner()

    mainGUI.title("RobotPy Drive Characterization Data Logger")

    configure_gui()

    mainGUI.mainloop()


if __name__ == "__main__":

    main()

    # log_datefmt = "%H:%M:%S"
    # log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"

    # logging.basicConfig(level=logging.INFO, datefmt=log_datefmt, format=log_format)

    # dl = DataLogger()
    # dl.run()
