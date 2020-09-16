# This GUI analyzes the data collected by the data logger.  Support is
# provided for both feedforward and feedback analysis, as well as diagnostic
# plotting.

import json
import math
import os
import tkinter
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

import control as cnt
import frccontrol as frccnt
import matplotlib

# This fixes a crash on macOS Mojave by using the TkAgg backend
# https://stackoverflow.com/a/34109240
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import numpy as np
import statsmodels.api as sm
from frc_characterization.utils import FloatEntry, IntEntry
from mpl_toolkits.mplot3d import Axes3D


class ProgramState:
    def __init__(self, dir):
        self.mainGUI = tkinter.Tk()

        self.project_path = StringVar(self.mainGUI)
        self.project_path.set(dir)

        self.window_size = IntVar(self.mainGUI)
        self.window_size.set(8)

        self.motion_threshold = DoubleVar(self.mainGUI)
        self.motion_threshold.set(0.2)

        self.subset = StringVar(self.mainGUI)
        self.subset.set("Forward")

        self.units = StringVar(self.mainGUI)
        self.units.set("Rotations")

        self.stored_data = None

        self.quasi_forward = None
        self.quasi_backward = None
        self.step_forward = None
        self.step_backward = None

        self.ks = DoubleVar(self.mainGUI)
        self.kv = DoubleVar(self.mainGUI)
        self.ka = DoubleVar(self.mainGUI)
        self.kcos = DoubleVar(self.mainGUI)
        self.r_square = DoubleVar(self.mainGUI)

        self.qp = DoubleVar(self.mainGUI)
        self.qp.set(1)

        self.qv = DoubleVar(self.mainGUI)
        self.qv.set(1.5)

        self.max_effort = DoubleVar(self.mainGUI)
        self.max_effort.set(7)

        self.period = DoubleVar(self.mainGUI)
        self.period.set(0.02)

        self.max_controller_output = DoubleVar(self.mainGUI)
        self.max_controller_output.set(12)

        self.controller_time_normalized = BooleanVar(self.mainGUI)
        self.controller_time_normalized.set(True)

        self.measurement_delay = DoubleVar(self.mainGUI)
        self.measurement_delay.set(0)

        self.gearing = DoubleVar(self.mainGUI)
        self.gearing.set(1)

        self.controller_type = StringVar(self.mainGUI)
        self.controller_type.set("Onboard")

        self.encoder_epr = IntVar(self.mainGUI)
        self.encoder_epr.set(4096)

        self.has_slave = BooleanVar(self.mainGUI)
        self.has_slave.set(False)

        self.slave_period = DoubleVar(self.mainGUI)
        self.slave_period.set(0.01)

        self.gain_units_preset = StringVar(self.mainGUI)
        self.gain_units_preset.set("Default")

        self.loop_type = StringVar(self.mainGUI)
        self.loop_type.set("Velocity")

        self.kp = DoubleVar(self.mainGUI)
        self.kd = DoubleVar(self.mainGUI)


# Set up main window


def configure_gui(STATE):
    def getFile():
        dataFile = tkinter.filedialog.askopenfile(
            parent=STATE.mainGUI,
            mode="rb",
            title="Choose the data file (.JSON)",
            initialdir=STATE.project_path.get(),
        )
        fileEntry.configure(state="normal")
        fileEntry.delete(0, END)
        fileEntry.insert(0, dataFile.name)
        fileEntry.configure(state="readonly")
        try:
            data = json.load(dataFile)

            try:
                # Transform the data into a numpy array to make it easier to use
                # -> transpose it so we can deal with it in columns
                for k in JSON_DATA_KEYS:
                    data[k] = np.array(data[k]).transpose()

                if len(data[JSON_DATA_KEYS[-1]]) > len(columns):
                    messagebox.showerror(
                        "Error!",
                        "You cannot import characterization data from a different mechanism.",
                    )
                    return

                STATE.stored_data = data

                analyzeButton.configure(state="normal")
            except Exception as e:
                messagebox.showerror(
                    "Error!",
                    "The structure of the data JSON was not recognized.\n"
                    + "Details\n"
                    + repr(e),
                )
                return
        except Exception as e:
            messagebox.showerror(
                "Error!",
                "The JSON file could not be loaded.\n" + "Details:\n" + repr(e),
                parent=STATE.mainGUI,
            )
            return

    def runAnalysis():

        (
            STATE.quasi_forward,
            STATE.quasi_backward,
            STATE.step_forward,
            STATE.step_backward,
        ) = prepare_data(STATE.stored_data, window=STATE.window_size.get(), STATE=STATE)

        if (
            STATE.quasi_forward is None
            or STATE.quasi_backward is None
            or STATE.step_forward is None
            or STATE.step_backward is None
        ):
            return

        if STATE.subset.get() == "Forward":
            ks, kv, ka, rsquare = calcFit(STATE.quasi_forward, STATE.step_forward)
        elif STATE.subset.get() == "Backward":
            ks, kv, ka, rsquare = calcFit(STATE.quasi_backward, STATE.step_backward)

        STATE.ks.set(float("%.3g" % ks))
        STATE.kv.set(float("%.3g" % kv))
        STATE.ka.set(float("%.3g" % ka))
        STATE.r_square.set(float("%.3g" % rsquare))

        calcGains()

        timePlotsButton.configure(state="normal")
        voltPlotsButton.configure(state="normal")
        fancyPlotButton.configure(state="normal")
        calcGainsButton.configure(state="normal")

    def plotTimeDomain():
        if STATE.subset.get() == "Forward":
            _plotTimeDomain("Forward", STATE.quasi_forward, STATE.step_forward)
        elif STATE.subset.get() == "Backward":
            _plotTimeDomain("Backward", STATE.quasi_backward, STATE.step_backward)

    def plotVoltageDomain():
        if STATE.subset.get() == "Forward":
            _plotVoltageDomain(
                "Forward", STATE.quasi_forward, STATE.step_forward, STATE
            )
        elif STATE.subset.get() == "Backward":
            _plotVoltageDomain(
                "Backward", STATE.quasi_backward, STATE.step_backward, STATE
            )

    def plot3D():
        if STATE.subset.get() == "Forward":
            _plot3D("Forward", STATE.quasi_forward, STATE.step_forward, STATE)
        elif STATE.subset.get() == "Backward":
            _plot3D("Backward", STATE.quasi_backward, STATE.step_backward, STATE)

    def calcGains():

        period = (
            STATE.period.get()
            if not STATE.has_slave.get()
            else STATE.slave_period.get()
        )

        if STATE.loop_type.get() == "Position":
            kp, kd = _calcGainsPos(
                STATE.kv.get(),
                STATE.ka.get(),
                STATE.qp.get(),
                STATE.qv.get(),
                STATE.max_effort.get(),
                period,
                STATE.measurement_delay.get(),
            )
        else:
            kp, kd = _calcGainsVel(
                STATE.kv.get(),
                STATE.ka.get(),
                STATE.qv.get(),
                STATE.max_effort.get(),
                period,
                STATE.measurement_delay.get(),
            )

        # Scale gains to output
        kp = kp / 12 * STATE.max_controller_output.get()
        kd = kd / 12 * STATE.max_controller_output.get()

        # Rescale kD if not time-normalized
        if not STATE.controller_time_normalized.get():
            kd = kd / STATE.period.get()

        # Get the correct conversion factor for rotations
        if STATE.units.get() == "Radians":
            rotation = 2 * math.pi
        elif STATE.units.get() == "Rotations":
            rotation = 1
        elif STATE.units.get() == "Degrees":
            rotation = 360

        # Convert to controller-native units
        if STATE.controller_type.get() == "Talon":
            kp = kp * rotation / (STATE.encoder_epr.get() * STATE.gearing.get())
            kd = kd * rotation / (STATE.encoder_epr.get() * STATE.gearing.get())
            if STATE.loop_type.get() == "Velocity":
                kp = kp * 10

        STATE.kp.set(float("%.3g" % kp))
        STATE.kd.set(float("%.3g" % kd))

    def presetGains(*args):
        def setMeasurementDelay(delay):
            STATE.measurement_delay.set(
                0 if STATE.loop_type.get() == "Position" else delay
            )

        # A number of motor controllers use moving average filters; these are types of FIR filters.
        # A moving average filter with a window size of N is a FIR filter with N taps.
        # The average delay (in taps) of an arbitrary FIR filter with N taps is (N-1)/2.
        # All of the delays below assume that 1 T takes 1 ms.
        #
        # Proof:
        # N taps with delays of 0 .. N - 1 T
        #
        # average delay = (sum 0 .. N - 1) / N T
        # = (sum 1 .. N - 1) / N T
        #
        # note: sum 1 .. n = n(n + 1) / 2
        #
        # = (N - 1)((N - 1) + 1) / (2N) T
        # = (N - 1)N / (2N) T
        # = (N - 1)/2 T

        presets = {
            "Default": lambda: (
                STATE.max_controller_output.set(12),
                STATE.period.set(0.02),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set("Onboard"),
                setMeasurementDelay(0),
            ),
            "WPILib (2020-)": lambda: (
                STATE.max_controller_output.set(12),
                STATE.period.set(0.02),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set("Onboard"),
                # Note that the user will need to remember to set this if the onboard controller is getting delayed measurements.
                setMeasurementDelay(0),
            ),
            "WPILib (Pre-2020)": lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(0.05),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set("Onboard"),
                # Note that the user will need to remember to set this if the onboard controller is getting delayed measurements.
                setMeasurementDelay(0),
            ),
            "Talon FX": lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(0.001),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set("Talon"),
                # https://phoenix-documentation.readthedocs.io/en/latest/ch14_MCSensor.html#changing-velocity-measurement-parameters
                # 100 ms sampling period + a moving average window size of 64 (i.e. a 64-tap FIR) = 100/2 ms + (64-1)/2 ms = 81.5 ms.
                # See above for more info on moving average delays.
                setMeasurementDelay(81.5),
            ),
            "Talon SRX (2020-)": lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(0.001),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set("Talon"),
                # https://phoenix-documentation.readthedocs.io/en/latest/ch14_MCSensor.html#changing-velocity-measurement-parameters
                # 100 ms sampling period + a moving average window size of 64 (i.e. a 64-tap FIR) = 100/2 ms + (64-1)/2 ms = 81.5 ms.
                # See above for more info on moving average delays.
                setMeasurementDelay(81.5),
            ),
            "Talon SRX (Pre-2020)": lambda: (
                STATE.max_controller_output.set(1023),
                STATE.period.set(0.001),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set("Talon"),
                # https://phoenix-documentation.readthedocs.io/en/latest/ch14_MCSensor.html#changing-velocity-measurement-parameters
                # 100 ms sampling period + a moving average window size of 64 (i.e. a 64-tap FIR) = 100/2 ms + (64-1)/2 ms = 81.5 ms.
                # See above for more info on moving average delays.
                setMeasurementDelay(81.5),
            ),
            "Spark MAX (brushless)": lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(0.001),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set("Spark"),
                # According to a Rev employee on the FRC Discord the window size is 40 so delay = (40-1)/2 ms = 19.5 ms.
                # See above for more info on moving average delays.
                setMeasurementDelay(19.5),
            ),
            "Spark MAX (brushed)": lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(0.001),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set("Spark"),
                # https://www.revrobotics.com/content/sw/max/sw-docs/cpp/classrev_1_1_c_a_n_encoder.html#a7e6ce792bc0c0558fb944771df572e6a
                # 64-tap FIR = (64-1)/2 ms = 31.5 ms delay.
                # See above for more info on moving average delays.
                setMeasurementDelay(31.5),
            ),
        }

        presets.get(STATE.gain_units_preset.get(), "Default")()

    def enableOffboard(*args):
        if STATE.controller_type.get() == "Onboard":
            gearingEntry.configure(state="disabled")
            eprEntry.configure(state="disabled")
            hasSlave.configure(state="disabled")
            slavePeriodEntry.configure(state="disabled")
        elif STATE.controller_type.get() == "Talon":
            gearingEntry.configure(state="normal")
            eprEntry.configure(state="normal")
            hasSlave.configure(state="normal")
            if STATE.has_slave.get():
                slavePeriodEntry.configure(state="normal")
            else:
                slavePeriodEntry.configure(state="disabled")
        else:
            gearingEntry.configure(state="disabled")
            eprEntry.configure(state="disabled")
            hasSlave.configure(state="normal")
            if STATE.has_slave.get():
                slavePeriodEntry.configure(state="normal")
            else:
                slavePeriodEntry.configure(state="disabled")

    def enableErrorBounds(*args):
        if STATE.loop_type.get() == "Position":
            qPEntry.configure(state="normal")
        else:
            qPEntry.configure(state="disabled")

    # TOP OF WINDOW (FILE SELECTION)

    topFrame = Frame(STATE.mainGUI)
    topFrame.grid(row=0, column=0, columnspan=4)

    Button(topFrame, text="Select Data File", command=getFile).grid(
        row=0, column=0, padx=4
    )

    fileEntry = Entry(topFrame, width=80)
    fileEntry.grid(row=0, column=1, columnspan=3)
    fileEntry.configure(state="readonly")

    # The only current option is rotations
    # This made the implementation of everything easier
    Label(topFrame, text="Units:", width=10).grid(row=0, column=4)
    unitChoices = {"Rotations", "Degrees", "Radians"}
    unitsMenu = OptionMenu(topFrame, STATE.units, *sorted(unitChoices))
    unitsMenu.configure(width=10)
    unitsMenu.grid(row=0, column=5, sticky="ew")

    Label(topFrame, text="Subset:", width=15).grid(row=0, column=6)
    subsets = {
        "Forward",
        "Backward",
    }
    dirMenu = OptionMenu(topFrame, STATE.subset, *sorted(subsets))
    dirMenu.configure(width=20)
    dirMenu.grid(row=0, column=7)

    for child in topFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    # FEEDFORWARD ANALYSIS FRAME

    ffFrame = Frame(STATE.mainGUI, bd=2, relief="groove")
    ffFrame.grid(row=1, column=0, columnspan=3, sticky="ns")

    Label(ffFrame, text="Feedforward Analysis").grid(row=0, column=0, columnspan=5)

    analyzeButton = Button(
        ffFrame, text="Analyze Data", command=runAnalysis, state="disabled"
    )
    analyzeButton.grid(row=1, column=0, sticky="ew")

    timePlotsButton = Button(
        ffFrame,
        text="Time-Domain Diagnostics",
        command=plotTimeDomain,
        state="disabled",
    )
    timePlotsButton.grid(row=2, column=0, sticky="ew")

    voltPlotsButton = Button(
        ffFrame,
        text="Voltage-Domain Diagnostics",
        command=plotVoltageDomain,
        state="disabled",
    )
    voltPlotsButton.grid(row=3, column=0, sticky="ew")

    fancyPlotButton = Button(
        ffFrame, text="3D Diagnostics", command=plot3D, state="disabled"
    )
    fancyPlotButton.grid(row=4, column=0, sticky="ew")

    Label(ffFrame, text="Accel Window Size:", anchor="e").grid(
        row=1, column=1, sticky="ew"
    )
    windowEntry = IntEntry(ffFrame, textvariable=STATE.window_size, width=5)
    windowEntry.grid(row=1, column=2)

    Label(ffFrame, text="Motion Threshold (units/s):", anchor="e").grid(
        row=2, column=1, sticky="ew"
    )
    thresholdEntry = FloatEntry(ffFrame, textvariable=STATE.motion_threshold, width=5)
    thresholdEntry.grid(row=2, column=2)

    Label(ffFrame, text="kS:", anchor="e").grid(row=1, column=3, sticky="ew")
    kSEntry = FloatEntry(ffFrame, textvariable=STATE.ks, width=10)
    kSEntry.grid(row=1, column=4)
    kSEntry.configure(state="readonly")

    Label(ffFrame, text="kV:", anchor="e").grid(row=2, column=3, sticky="ew")
    kVEntry = FloatEntry(ffFrame, textvariable=STATE.kv, width=10)
    kVEntry.grid(row=2, column=4)
    kVEntry.configure(state="readonly")

    Label(ffFrame, text="kA:", anchor="e").grid(row=3, column=3, sticky="ew")
    kAEntry = FloatEntry(ffFrame, textvariable=STATE.ka, width=10)
    kAEntry.grid(row=3, column=4)
    kAEntry.configure(state="readonly")

    Label(ffFrame, text="r-squared:", anchor="e").grid(row=4, column=3, sticky="ew")
    rSquareEntry = FloatEntry(ffFrame, textvariable=STATE.r_square, width=10)
    rSquareEntry.grid(row=4, column=4)
    rSquareEntry.configure(state="readonly")

    for child in ffFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)

    # FEEDBACK ANALYSIS FRAME

    fbFrame = Frame(STATE.mainGUI, bd=2, relief="groove")
    fbFrame.grid(row=1, column=3, columnspan=5)

    Label(fbFrame, text="Feedback Analysis").grid(row=0, column=0, columnspan=5)

    Label(fbFrame, text="Gain Settings Preset:", anchor="e").grid(
        row=1, column=0, sticky="ew"
    )
    presetChoices = {
        "Default",
        "WPILib (2020-)",
        "WPILib (Pre-2020)",
        "Talon FX",
        "Talon SRX (2020-)",
        "Talon SRX (Pre-2020)",
        "Spark MAX (brushless)",
        "Spark MAX (brushed)",
    }
    presetMenu = OptionMenu(fbFrame, STATE.gain_units_preset, *sorted(presetChoices))
    presetMenu.grid(row=1, column=1)
    presetMenu.config(width=12)
    STATE.gain_units_preset.trace_add("write", presetGains)

    Label(fbFrame, text="Controller Period (s):", anchor="e").grid(
        row=2, column=0, sticky="ew"
    )
    periodEntry = FloatEntry(fbFrame, textvariable=STATE.period, width=10)
    periodEntry.grid(row=2, column=1)

    Label(fbFrame, text="Max Controller Output:", anchor="e").grid(
        row=3, column=0, sticky="ew"
    )
    controllerMaxEntry = FloatEntry(
        fbFrame, textvariable=STATE.max_controller_output, width=10
    )
    controllerMaxEntry.grid(row=3, column=1)

    Label(fbFrame, text="Time-Normalized Controller:", anchor="e").grid(
        row=4, column=0, sticky="ew"
    )
    normalizedButton = Checkbutton(fbFrame, variable=STATE.controller_time_normalized)
    normalizedButton.grid(row=4, column=1)

    Label(fbFrame, text="Controller Type:", anchor="e").grid(
        row=5, column=0, sticky="ew"
    )
    controllerTypes = {"Onboard", "Talon", "Spark"}
    controllerTypeMenu = OptionMenu(
        fbFrame, STATE.controller_type, *sorted(controllerTypes)
    )
    controllerTypeMenu.grid(row=5, column=1)
    STATE.controller_type.trace_add("write", enableOffboard)

    Label(fbFrame, text="Measurement delay (ms):", anchor="e").grid(
        row=6, column=0, sticky="ew"
    )
    velocityDelay = FloatEntry(fbFrame, textvariable=STATE.measurement_delay, width=10)
    velocityDelay.grid(row=6, column=1)

    Label(fbFrame, text="Post-Encoder Gearing:", anchor="e").grid(
        row=7, column=0, sticky="ew"
    )
    gearingEntry = FloatEntry(fbFrame, textvariable=STATE.gearing, width=10)
    gearingEntry.configure(state="disabled")
    gearingEntry.grid(row=7, column=1)

    Label(fbFrame, text="Encoder EPR:", anchor="e").grid(row=8, column=0, sticky="ew")
    eprEntry = IntEntry(fbFrame, textvariable=STATE.encoder_epr, width=10)
    eprEntry.configure(state="disabled")
    eprEntry.grid(row=8, column=1)

    Label(fbFrame, text="Has Slave:", anchor="e").grid(row=9, column=0, sticky="ew")
    hasSlave = Checkbutton(fbFrame, variable=STATE.has_slave)
    hasSlave.grid(row=9, column=1)
    hasSlave.configure(state="disabled")
    STATE.has_slave.trace_add("write", enableOffboard)

    Label(fbFrame, text="Slave Update Period (s):", anchor="e").grid(
        row=10, column=0, sticky="ew"
    )
    slavePeriodEntry = FloatEntry(fbFrame, textvariable=STATE.slave_period, width=10)
    slavePeriodEntry.grid(row=10, column=1)
    slavePeriodEntry.configure(state="disabled")

    Label(fbFrame, text="Max Acceptable Position Error (units):", anchor="e").grid(
        row=1, column=2, columnspan=2, sticky="ew"
    )
    qPEntry = FloatEntry(fbFrame, textvariable=STATE.qp, width=10)
    qPEntry.grid(row=1, column=4)
    qPEntry.configure(state="disabled")

    Label(fbFrame, text="Max Acceptable Velocity Error (units/s):", anchor="e").grid(
        row=2, column=2, columnspan=2, sticky="ew"
    )
    qVEntry = FloatEntry(fbFrame, textvariable=STATE.qv, width=10)
    qVEntry.grid(row=2, column=4)

    Label(fbFrame, text="Max Acceptable Control Effort (V):", anchor="e").grid(
        row=3, column=2, columnspan=2, sticky="ew"
    )
    effortEntry = FloatEntry(fbFrame, textvariable=STATE.max_effort, width=10)
    effortEntry.grid(row=3, column=4)

    Label(fbFrame, text="Loop Type:", anchor="e").grid(
        row=4, column=2, columnspan=2, sticky="ew"
    )
    loopTypes = {"Position", "Velocity"}
    loopTypeMenu = OptionMenu(fbFrame, STATE.loop_type, *sorted(loopTypes))
    loopTypeMenu.configure(width=8)
    loopTypeMenu.grid(row=4, column=4)
    STATE.loop_type.trace_add("write", enableErrorBounds)
    # We reset everything to the selected preset when the user changes the loop type
    # This prevents people from forgetting to change measurement delays
    STATE.loop_type.trace_add("write", presetGains)

    Label(fbFrame, text="kV:", anchor="e").grid(row=5, column=2, sticky="ew")
    kVFBEntry = FloatEntry(fbFrame, textvariable=STATE.kv, width=10)
    kVFBEntry.grid(row=5, column=3)
    Label(fbFrame, text="kA:", anchor="e").grid(row=6, column=2, sticky="ew")
    kAFBEntry = FloatEntry(fbFrame, textvariable=STATE.ka, width=10)
    kAFBEntry.grid(row=6, column=3)

    calcGainsButton = Button(
        fbFrame,
        text="Calculate Optimal Controller Gains",
        command=calcGains,
        state="disabled",
    )
    calcGainsButton.grid(row=7, column=2, columnspan=3)

    Label(fbFrame, text="kP:", anchor="e").grid(row=8, column=2, sticky="ew")
    kPEntry = FloatEntry(
        fbFrame, textvariable=STATE.kp, width=10, state="readonly"
    ).grid(row=8, column=3)

    Label(fbFrame, text="kD:", anchor="e").grid(row=9, column=2, sticky="ew")
    kDEntry = FloatEntry(
        fbFrame, textvariable=STATE.kd, width=10, state="readonly"
    ).grid(row=9, column=3)

    for child in fbFrame.winfo_children():
        child.grid_configure(padx=1, pady=1)


#
# These parameters are used to indicate which column of data each parameter
# can be found at
#


columns = dict(time=0, battery=1, autospeed=2, volts=3, encoder_pos=4, encoder_vel=5)

# These are the indices of data stored in the json file
TIME_COL = columns["time"]
BATTERY_COL = columns["battery"]
AUTOSPEED_COL = columns["autospeed"]
VOLTS_COL = columns["volts"]
ENCODER_P_COL = columns["encoder_pos"]
ENCODER_V_COL = columns["encoder_vel"]

# The are the indices of data returned from prepare_data function
PREPARED_TM_COL = 0
PREPARED_V_COL = 1
PREPARED_POS_COL = 2
PREPARED_VEL_COL = 3
PREPARED_ACC_COL = 4

PREPARED_MAX_COL = PREPARED_ACC_COL

JSON_DATA_KEYS = ["slow-forward", "slow-backward", "fast-forward", "fast-backward"]

# From 449's R script (note: R is 1-indexed)


def smoothDerivative(tm, value, n):
    """
    :param tm: time column
    :param value: Value to take the derivative of
    :param n: smoothing parameter
    """
    dlen = len(value)
    dt = tm[n:dlen] - tm[: (dlen - n)]
    x = (value[(n):dlen] - value[: (dlen - n)]) / dt

    # pad to original length by adding zeros on either side
    return np.pad(x, (int(np.ceil(n / 2.0)), int(np.floor(n / 2.0))), mode="constant")


def trim_quasi_testdata(data, STATE):
    adata = np.abs(data)
    truth = np.all(
        [
            adata[ENCODER_V_COL] > STATE.motion_threshold.get(),
            adata[VOLTS_COL] > 0,
        ],
        axis=0,
    )

    temp = data.transpose()[truth].transpose()

    if temp[TIME_COL].size == 0:
        messagebox.showinfo(
            "Error!",
            "No data in quasistatic test is above motion threshold. "
            + "Try running with a smaller motion threshold (use --motion_threshold) "
            + "and make sure your encoder is reporting correctly!",
        )
        return None
    else:
        return temp


def trim_step_testdata(data):
    # removes anything before the max acceleration
    max_accel_idx = np.argmax(np.abs(data[PREPARED_ACC_COL]))
    return data[:, max_accel_idx + 1 :]


def compute_accel(data, window):
    """
    Returned data columns correspond to PREPARED_*
    """

    # deal with incomplete data
    if len(data[TIME_COL]) < window * 2:
        messagebox.showinfo(
            "Error!",
            "Not enough data points to compute acceleration. "
            + "Try running with a smaller window setting or a smaller threshold.",
        )
        return None

    # Compute left/right acceleration
    acc = smoothDerivative(data[TIME_COL], data[ENCODER_V_COL], window)

    return np.vstack(
        (
            data[TIME_COL],
            data[VOLTS_COL],
            data[ENCODER_P_COL],
            data[ENCODER_V_COL],
            acc,
        )
    )


def prepare_data(data, window, STATE):
    """
    Firstly, data should be 'trimmed' to exclude any data points at which the
    robot was not being commanded to do anything.

    Secondly, robot acceleration should be calculated from robot velocity and time.
    We have found it effective to do this by taking the slope of the secant line
    of velocity over a 60ms (3 standard loop iterations) window.

    Thirdly, data from the quasi-static test should be trimmed to exclude the
    initial period in which the robot is not moving due to static friction
    Fourthly, data from the step-voltage acceleration tests must be trimmed to
    remove the initial 'ramp-up' period that exists due to motor inductance; this
    can be done by simply removing all data points before maximum acceleration is
    reached.

    Finally, the data can be analyzed: pool your trimmed data into four data sets
    - one for each side of the robot (left or right) and each direction (forwards
    or backwards).

    For each set, run a linear regression of voltage seen at the motor
    (or battery voltage if you do not have Talon SRXs) versus velocity and
    acceleration.

    Voltage should be in units of volts, velocity in units of feet per second,
    and acceleration in units of feet per second squared.

    Each data pool will then yield three parameters -
    intercept, Kv (the regression coefficient of velocity), and Ka (the regression
    coefficient of acceleration).
    """

    # ensure voltage sign matches velocity sign

    for x in JSON_DATA_KEYS:
        data[x][VOLTS_COL] = np.copysign(data[x][VOLTS_COL], data[x][ENCODER_V_COL])

    # trim quasi data before computing acceleration
    sf_trim = trim_quasi_testdata(data["slow-forward"], STATE)
    sb_trim = trim_quasi_testdata(data["slow-backward"], STATE)

    if sf_trim is None or sb_trim is None:
        return [None] * 8

    sf = compute_accel(sf_trim, window)
    sb = compute_accel(sb_trim, window)

    if sf is None or sb is None:
        return [None] * 8

    # trim step data after computing acceleration
    ff = compute_accel(data["fast-forward"], window)
    fb = compute_accel(data["fast-backward"], window)

    if ff is None or fb is None:
        return [None] * 8

    ff = trim_step_testdata(ff)
    fb = trim_step_testdata(fb)

    return sf, sb, ff, fb


def ols(x1, x2, y):
    """multivariate linear regression using ordinary least squares"""
    x = np.array((np.sign(x1), x1, x2)).T
    model = sm.OLS(y, x)
    return model.fit()


def _plotTimeDomain(subset, qu, step):
    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    # Time-domain plots.
    # These should show if anything went horribly wrong during the tests.
    # Useful for diagnosing the data trim; quasistatic test should look purely linear with no leading 'tail'

    plt.figure(subset + " Time-Domain Plots")

    # quasistatic vel and accel vs time
    ax1 = plt.subplot(221)
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Velocity")
    ax1.set_title("Quasistatic velocity vs time")
    plt.scatter(qu[PREPARED_TM_COL], qu[PREPARED_VEL_COL], marker=".", c="#000000")

    ax = plt.subplot(222, sharey=ax1)
    ax.set_xlabel("Time")
    ax.set_ylabel("Velocity")
    ax.set_title("Dynamic velocity vs time")
    plt.scatter(step[PREPARED_TM_COL], step[PREPARED_VEL_COL], marker=".", c="#000000")

    # dynamic vel and accel vs time
    ax2 = plt.subplot(223)
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Acceleration")
    ax2.set_title("Quasistatic acceleration vs time")
    plt.scatter(qu[PREPARED_TM_COL], qu[PREPARED_ACC_COL], marker=".", c="#000000")

    ax = plt.subplot(224, sharey=ax2)
    ax.set_xlabel("Time")
    ax.set_ylabel("Acceleration")
    ax.set_title("Dynamic acceleration vs time")
    plt.scatter(step[PREPARED_TM_COL], step[PREPARED_ACC_COL], marker=".", c="#000000")

    # Fix overlapping axis labels
    plt.tight_layout(pad=0.5)

    plt.show()


def _plotVoltageDomain(subset, qu, step, STATE):

    # Voltage-domain plots
    # These should show linearity of velocity/acceleration data with voltage
    # X-axis is not raw voltage, but rather 'portion of voltage corresponding to vel/acc'
    # Both plots should be straight lines through the origin
    # Fit lines will be straight lines through the origin by construction; data should match fit

    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    ks = STATE.ks.get()
    kv = STATE.kv.get()
    ka = STATE.ka.get()
    r_square = STATE.r_square.get()

    plt.figure(subset + " Voltage-Domain Plots")

    # quasistatic vel vs. vel-causing voltage
    ax = plt.subplot(211)
    ax.set_xlabel("Velocity-Portion Voltage")
    ax.set_ylabel("Velocity")
    ax.set_title("Quasistatic velocity vs velocity-portion voltage")
    plt.scatter(
        qu[PREPARED_V_COL]
        - ks * np.sign(qu[PREPARED_VEL_COL])
        - ka * qu[PREPARED_ACC_COL],
        qu[PREPARED_VEL_COL],
        marker=".",
        c="#000000",
    )

    # show fit line from multiple regression
    y = np.linspace(np.min(qu[PREPARED_VEL_COL]), np.max(qu[PREPARED_VEL_COL]))
    plt.plot(kv * y, y)

    # dynamic accel vs. accel-causing voltage
    ax = plt.subplot(212)
    ax.set_xlabel("Acceleration-Portion Voltage")
    ax.set_ylabel("Acceleration")
    ax.set_title("Dynamic acceleration vs acceleration-portion voltage")
    plt.scatter(
        step[PREPARED_V_COL]
        - ks * np.sign(step[PREPARED_VEL_COL])
        - kv * step[PREPARED_VEL_COL],
        step[PREPARED_ACC_COL],
        marker=".",
        c="#000000",
    )

    # show fit line from multiple regression
    y = np.linspace(np.min(step[PREPARED_ACC_COL]), np.max(step[PREPARED_ACC_COL]))
    plt.plot(ka * y, y)

    # Fix overlapping axis labels
    plt.tight_layout(pad=0.5)

    plt.show()


def _plot3D(subset, qu, step, STATE):

    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    ks = STATE.ks.get()
    kv = STATE.kv.get()
    ka = STATE.ka.get()
    kcos = STATE.kcos.get()
    r_square = STATE.r_square.get()

    # Interactive 3d plot of voltage over entire vel-accel plane
    # Really cool, not really any more diagnostically-useful than prior plots but worth seeing
    plt.figure(subset + " 3D Vel-Accel Plane Plot")

    ax = plt.subplot(111, projection="3d")

    # 3D scatterplot
    ax.set_xlabel("Velocity")
    ax.set_ylabel("Acceleration")
    ax.set_zlabel("Voltage")
    ax.set_title("Voltage vs velocity and acceleration")
    ax.scatter(vel, accel, volts)

    # Show best fit plane
    vv, aa = np.meshgrid(
        np.linspace(np.min(vel), np.max(vel)), np.linspace(np.min(accel), np.max(accel))
    )
    ax.plot_surface(
        vv, aa, ks * np.sign(vv) + kv * vv + ka * aa, alpha=0.2, color=[0, 1, 1]
    )

    plt.show()


def calcFit(qu, step):
    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    fit = ols(vel, accel, volts)
    ks, kv, ka = fit.params
    rsquare = fit.rsquared

    return ks, kv, ka, rsquare


def _calcGainsPos(kv, ka, qp, qv, effort, period, position_delay):

    # If acceleration requires no effort, velocity becomes an input for position
    # control. We choose an appropriate model in this case to avoid numerical
    # instabilities in LQR.
    if ka > 1e-7:
        A = np.array([[0, 1], [0, -kv / ka]])
        B = np.array([[0], [1 / ka]])
        C = np.array([[1, 0]])
        D = np.array([[0]])

        q = [qp, qv]  # units and units/s acceptable errors
        r = [effort]  # V acceptable actuation effort
    else:
        A = np.array([[0]])
        B = np.array([[1]])
        C = np.array([[1]])
        D = np.array([[0]])

        q = [qp]  # units acceptable error
        r = [qv]  # units/s acceptable error
    sys = cnt.ss(A, B, C, D)
    dsys = sys.sample(period)

    # Assign Q and R matrices according to Bryson's rule [1]. The elements
    # of q and r are tunable by the user.
    #
    # [1] 'Bryson's rule' in
    #     https://file.tavsys.net/control/state-space-guide.pdf
    Q = np.diag(1.0 / np.square(q))
    R = np.diag(1.0 / np.square(r))
    K = frccnt.lqr(dsys, Q, R)

    if position_delay > 0:
        # This corrects the gain to compensate for measurement delay, which
        # can be quite large as a result of filtering for some motor
        # controller and sensor combinations. Note that this will result in
        # an overly conservative (i.e. non-optimal) gain, because we need to
        # have a time-varying control gain to give the system an initial kick
        # in the right direction. The state will converge to zero and the
        # controller gain will converge to the steady-state one the tool outputs.
        #
        # See E.4.2 in
        #   https://file.tavsys.net/control/controls-engineering-in-frc.pdf
        delay_in_seconds = position_delay / 1000  # ms -> s
        K = K @ np.linalg.matrix_power(
            dsys.A - dsys.B @ K, round(delay_in_seconds / period)
        )

    # With the alternate model, `kp = kv * K[0, 0]` is used because the gain
    # produced by LQR is for velocity. We can use the feedforward equation
    # `u = kv * v` to convert velocity to voltage. `kd = 0` because velocity
    # was an input; we don't need feedback control to command it.
    if ka > 1e-7:
        kp = K[0, 0]
        kd = K[0, 1]
    else:
        kp = kv * K[0, 0]
        kd = 0

    return kp, kd


def _calcGainsVel(kv, ka, qv, effort, period, velocity_delay):

    # If acceleration for velocity control requires no effort, the feedback
    # control gains approach zero. We special-case it here because numerical
    # instabilities arise in LQR otherwise.
    if ka < 1e-7:
        return 0, 0

    A = np.array([[-kv / ka]])
    B = np.array([[1 / ka]])
    C = np.array([[1]])
    D = np.array([[0]])
    sys = cnt.ss(A, B, C, D)
    dsys = sys.sample(period)

    # Assign Q and R matrices according to Bryson's rule [1]. The elements
    # of q and r are tunable by the user.
    #
    # [1] 'Bryson's rule' in
    #     https://file.tavsys.net/control/state-space-guide.pdf
    q = [qv]  # units/s acceptable error
    r = [effort]  # V acceptable actuation effort
    Q = np.diag(1.0 / np.square(q))
    R = np.diag(1.0 / np.square(r))
    K = frccnt.lqr(dsys, Q, R)

    if velocity_delay > 0:
        # This corrects the gain to compensate for measurement delay, which
        # can be quite large as a result of filtering for some motor
        # controller and sensor combinations. Note that this will result in
        # an overly conservative (i.e. non-optimal) gain, because we need to
        # have a time-varying control gain to give the system an initial kick
        # in the right direction. The state will converge to zero and the
        # controller gain will converge to the steady-state one the tool outputs.
        #
        # See E.4.2 in
        #   https://file.tavsys.net/control/controls-engineering-in-frc.pdf
        delay_in_seconds = velocity_delay / 1000  # ms -> s
        K = K @ np.linalg.matrix_power(
            dsys.A - dsys.B @ K, round(delay_in_seconds / period)
        )

    kp = K[0, 0]
    kd = 0

    return kp, kd


def main(dir):

    STATE = ProgramState(dir)

    STATE.mainGUI.title("FRC Simple Motor Characterization Tool")

    configure_gui(STATE)
    STATE.mainGUI.mainloop()


if __name__ == "__main__":
    main(os.getcwd())
