# This GUI analyzes the data collected by the data logger.  Support is
# provided for both feedforward and feedback analysis, as well as diagnostic
# plotting.

import copy
import json
import logging
import math
import os
import tkinter
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

import control as cnt
import frccontrol as frccnt
import matplotlib
import pint

# This fixes a crash on macOS Mojave by using the TkAgg backend
# https://stackoverflow.com/a/34109240
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import numpy as np
import statsmodels.api as sm
from frc_characterization.newproject import Tests, Units
from frc_characterization.utils import FloatEntry, IntEntry
from mpl_toolkits.mplot3d import Axes3D

logger = logging.getLogger("logger")
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"

logging.basicConfig(level=logging.INFO, format=log_format)

# These are the indices of data stored in the json file
TIME_COL = 0
BATTERY_COL = 1
AUTOSPEED_COL = 2
L_VOLTS_COL = 3
R_VOLTS_COL = 4
L_ENCODER_P_COL = 5
R_ENCODER_P_COL = 6
L_ENCODER_V_COL = 7
R_ENCODER_V_COL = 8
GYRO_ANGLE_COL = 9

# The are the indices of data returned from prepare_data function
PREPARED_TM_COL = 0
PREPARED_V_COL = 1
PREPARED_POS_COL = 2
PREPARED_VEL_COL = 3
PREPARED_ACC_COL = 4
PREPARED_COS_COL = 5

PREPARED_MAX_COL = PREPARED_ACC_COL

JSON_DATA_KEYS = ["slow-forward", "slow-backward", "fast-forward", "fast-backward"]


class Analyzer:
    def __init__(self, dir):
        self.mainGUI = tkinter.Tk()

        self.project_path = StringVar(self.mainGUI)
        self.project_path.set(dir)

        self.window_size = IntVar(self.mainGUI)
        self.window_size.set(8)

        self.motion_threshold = DoubleVar(self.mainGUI)
        self.motion_threshold.set(0.2)

        self.subset = StringVar(self.mainGUI)

        self.units = StringVar(self.mainGUI)
        self.units.set(Units.FEET.value)

        self.track_width = DoubleVar(self.mainGUI)
        self.track_width.set("N/A")

        self.stored_data = None

        self.prepared_data = None

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

        self.has_follower = BooleanVar(self.mainGUI)
        self.has_follower.set(False)

        self.follower_period = DoubleVar(self.mainGUI)
        self.follower_period.set(0.01)

        self.gain_units_preset = StringVar(self.mainGUI)
        self.gain_units_preset.set("Default")

        self.loop_type = StringVar(self.mainGUI)
        self.loop_type.set("Velocity")

        self.kp = DoubleVar(self.mainGUI)
        self.kd = DoubleVar(self.mainGUI)

        self.test = StringVar(self.mainGUI)
        self.kg = DoubleVar(self.mainGUI)
        self.kcos = DoubleVar(self.mainGUI)

        self.units_per_rot = DoubleVar(self.mainGUI)

        self.convert_gains = BooleanVar(self.mainGUI)

    # Set up main window

    def configure_gui(self):
        def getFile():
            dataFile = tkinter.filedialog.askopenfile(
                parent=self.mainGUI,
                mode="rb",
                title="Choose the data file (.JSON)",
                initialdir=self.project_path.get(),
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

                    self.stored_data = data
                    logger.info("Received Data!")

                    analyzeButton.configure(state="normal")
                    self.units.set(data["units"])
                    self.test.set(data["test"])
                    self.units_per_rot.set(float(data["unitsPerRotation"]))
                    logger.info(
                        "Units: %s, Test: %s, Units per rotation: %.3f",
                        self.units.get(),
                        self.test.get(),
                        self.units_per_rot.get(),
                    )
                    initialUnitEnable()
                    enableUnitsPerRot()
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
                    parent=self.mainGUI,
                )
                return

        def runAnalysis():
            test_runners = {
                Tests.DRIVETRAIN: runAnalysisDrive,
                Tests.ELEVATOR: runAnalysisElevator,
                Tests.ARM: runAnalysisArm,
                Tests.SIMPLE_MOTOR: runAnalysisSimple,
            }

            self.prepared_data = self.prepare_data(
                self.stored_data, window=self.window_size.get()
            )

            if not self.prepared_data["Valid"]:
                return

            test_runners[Tests(self.test.get())]()
            convertGains.configure(state="normal")

            calcGains()

            timePlotsButton.configure(state="normal")
            voltPlotsButton.configure(state="normal")
            fancyPlotButton.configure(state="normal")
            calcGainsButton.configure(state="normal")

        def runAnalysisDrive():
            ks, kv, ka, rsquare = self.calcFit(
                *self.prepared_data[self.subset.get()], self.test.get()
            )

            self.ks.set(float("%.3g" % ks))
            self.kv.set(float("%.3g" % kv))
            self.ka.set(float("%.3g" % ka))
            self.r_square.set(float("%.3g" % rsquare))

            if "track-width" in self.stored_data:
                self.track_width.set(calcTrackWidth(self.stored_data["track-width"]))
            else:
                self.track_width.set("N/A")

        def runAnalysisElevator():
            kg, kfr, kv, ka, rsquare = self.calcFit(
                *self.prepared_data[self.subset.get()], self.test.get()
            )

            self.kg.set(float("%.3g" % kg))
            self.ks.set(float("%.3g" % kfr))
            self.kv.set(float("%.3g" % kv))
            self.ka.set(float("%.3g" % ka))
            self.r_square.set(float("%.3g" % rsquare))

        def runAnalysisArm():
            ks, kv, ka, kcos, rsquare = self.calcFit(
                *self.prepared_data[self.subset.get()], self.test.get()
            )

            self.ks.set(float("%.3g" % ks))
            self.kv.set(float("%.3g" % kv))
            self.ka.set(float("%.3g" % ka))
            self.kcos.set(float("%.3g" % kcos))
            self.r_square.set(float("%.3g" % rsquare))

        def runAnalysisSimple():
            ks, kv, ka, rsquare = self.calcFit(
                *self.prepared_data[self.subset.get()], self.test.get()
            )

            self.ks.set(float("%.3g" % ks))
            self.kv.set(float("%.3g" % kv))
            self.ka.set(float("%.3g" % ka))
            self.r_square.set(float("%.3g" % rsquare))

        def plotTimeDomain():
            subset = self.subset.get()
            self._plotTimeDomain(subset, *self.prepared_data[subset])

        def plotVoltageDomain():
            subset = self.subset.get()
            self._plotVoltageDomain(subset, *self.prepared_data[subset])

        def plot3D():
            subset = self.subset.get()
            self._plot3D(subset, *self.prepared_data[subset])

        def calcGains():

            period = (
                self.period.get()
                if not self.has_follower.get()
                else self.follower_period.get()
            )

            if self.loop_type.get() == "Position":
                kp, kd = self._calcGainsPos(
                    self.kv.get(),
                    self.ka.get(),
                    self.qp.get(),
                    self.qv.get(),
                    self.max_effort.get(),
                    period,
                    self.measurement_delay.get(),
                )
            else:
                kp, kd = self._calcGainsVel(
                    self.kv.get(),
                    self.ka.get(),
                    self.qv.get(),
                    self.max_effort.get(),
                    period,
                    self.measurement_delay.get(),
                )

            # Scale gains to output
            kp = kp / 12 * self.max_controller_output.get()
            kd = kd / 12 * self.max_controller_output.get()

            # Rescale kD if not time-normalized
            if not self.controller_time_normalized.get():
                kd = kd / self.period.get()

            # Get correct conversion factor for rotations
            units = Units(self.units.get())
            rotation = 0
            if isRotation(units.value):
                rotation = (1 * Units.ROTATIONS.unit).to(units.unit)
            else:
                rotation = self.units_per_rot.get()

            # Convert to controller-native units if desired
            if self.convert_gains.get():
                if self.controller_type.get() == "Talon":
                    kp = kp * rotation / (self.encoder_epr.get() * self.gearing.get())
                    kd = kd * rotation / (self.encoder_epr.get() * self.gearing.get())
                    if self.loop_type.get() == "Velocity":
                        kp = kp * 10
                if self.controller_type.get() == "Spark":
                    kp = kp / (self.gearing.get())
                    kd = kd / (self.gearing.get())
                    if self.loop_type.get() == "Velocity":
                        kp = kp / 60

            self.kp.set(float("%.3g" % kp))
            self.kd.set(float("%.3g" % kd))

        def calcTrackWidth(table):

            units = Units(self.units.get())

            # Doesn't run calculations if the units are rotational
            if isRotation(units.value):
                return "N/A"

            # Get conversion factor
            conversion_factor = 1

            initial_units = Units(self.stored_data["units"])

            # handle the case where data recorded only rotational
            if isRotation(self.stored_data["units"]):
                # Convert to Rotations
                units_per_rotation = (
                    (self.stored_data["unitsPerRotation"] * initial_units.unit)
                    .to(Units.ROTATIONS.unit)
                    .magnitude
                )

                # Convert to distance
                conversion_factor = round(
                    units_per_rotation * self.units_per_rot.get(), 3
                )
            else:
                conversion_factor = self.units_per_rot.get()

            # Note that this assumes the gyro angle is not modded (i.e. on [0, +infinity)),
            # and that a positive angle travels in the counter-clockwise direction

            d_left = (
                table[-1][R_ENCODER_P_COL] - table[0][R_ENCODER_P_COL]
            ) * conversion_factor
            d_right = (
                table[-1][L_ENCODER_P_COL] - table[0][L_ENCODER_P_COL]
            ) * conversion_factor
            d_angle = table[-1][GYRO_ANGLE_COL] - table[0][GYRO_ANGLE_COL]

            if d_angle == 0:
                messagebox.showerror(
                    "Error!",
                    "Change in gyro angle was 0... Is your gyro set up correctly?",
                )
                return 0.0

            # The below comes from solving ω=(vr−vl)/2r for 2r
            # Absolute values used to ensure the calculated value is always positive
            # and to add robustness to sensor inversion
            diameter = (abs(d_left) + abs(d_right)) / abs(d_angle)

            return diameter

        def presetGains(*args):
            def setMeasurementDelay(delay):
                self.measurement_delay.set(
                    0 if self.loop_type.get() == "Position" else delay
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
                    self.max_controller_output.set(12),
                    self.period.set(0.02),
                    self.controller_time_normalized.set(True),
                    self.controller_type.set("Onboard"),
                    setMeasurementDelay(0),
                ),
                "WPILib (2020-)": lambda: (
                    self.max_controller_output.set(12),
                    self.period.set(0.02),
                    self.controller_time_normalized.set(True),
                    self.controller_type.set("Onboard"),
                    # Note that the user will need to remember to set this if the onboard controller is getting delayed measurements.
                    setMeasurementDelay(0),
                ),
                "WPILib (Pre-2020)": lambda: (
                    self.max_controller_output.set(1),
                    self.period.set(0.05),
                    self.controller_time_normalized.set(False),
                    self.controller_type.set("Onboard"),
                    # Note that the user will need to remember to set this if the onboard controller is getting delayed measurements.
                    setMeasurementDelay(0),
                ),
                "Talon FX": lambda: (
                    self.max_controller_output.set(1),
                    self.period.set(0.001),
                    self.controller_time_normalized.set(True),
                    self.controller_type.set("Talon"),
                    # https://phoenix-documentation.readthedocs.io/en/latest/ch14_MCSensor.html#changing-velocity-measurement-parameters
                    # 100 ms sampling period + a moving average window size of 64 (i.e. a 64-tap FIR) = 100/2 ms + (64-1)/2 ms = 81.5 ms.
                    # See above for more info on moving average delays.
                    setMeasurementDelay(81.5),
                ),
                "Talon SRX (2020-)": lambda: (
                    self.max_controller_output.set(1),
                    self.period.set(0.001),
                    self.controller_time_normalized.set(True),
                    self.controller_type.set("Talon"),
                    # https://phoenix-documentation.readthedocs.io/en/latest/ch14_MCSensor.html#changing-velocity-measurement-parameters
                    # 100 ms sampling period + a moving average window size of 64 (i.e. a 64-tap FIR) = 100/2 ms + (64-1)/2 ms = 81.5 ms.
                    # See above for more info on moving average delays.
                    setMeasurementDelay(81.5),
                ),
                "Talon SRX (Pre-2020)": lambda: (
                    self.max_controller_output.set(1023),
                    self.period.set(0.001),
                    self.controller_time_normalized.set(False),
                    self.controller_type.set("Talon"),
                    # https://phoenix-documentation.readthedocs.io/en/latest/ch14_MCSensor.html#changing-velocity-measurement-parameters
                    # 100 ms sampling period + a moving average window size of 64 (i.e. a 64-tap FIR) = 100/2 ms + (64-1)/2 ms = 81.5 ms.
                    # See above for more info on moving average delays.
                    setMeasurementDelay(81.5),
                ),
                "Spark MAX (brushless)": lambda: (
                    self.max_controller_output.set(1),
                    self.period.set(0.001),
                    self.controller_time_normalized.set(False),
                    self.controller_type.set("Spark"),
                    # According to a Rev employee on the FRC Discord the window size is 40 so delay = (40-1)/2 ms = 19.5 ms.
                    # See above for more info on moving average delays.
                    setMeasurementDelay(19.5),
                ),
                "Spark MAX (brushed)": lambda: (
                    self.max_controller_output.set(1),
                    self.period.set(0.001),
                    self.controller_time_normalized.set(False),
                    self.controller_type.set("Spark"),
                    # https://www.revrobotics.com/content/sw/max/sw-docs/cpp/classrev_1_1_c_a_n_encoder.html#a7e6ce792bc0c0558fb944771df572e6a
                    # 64-tap FIR = (64-1)/2 ms = 31.5 ms delay.
                    # See above for more info on moving average delays.
                    setMeasurementDelay(31.5),
                ),
            }

            presets.get(self.gain_units_preset.get(), "Default")()
            if (
                "Talon" in self.gain_units_preset.get()
                or "Spark" in self.gain_units_preset.get()
            ):
                self.convert_gains.set(True)
            else:
                self.convert_gains.set(False)

        def enableOffboard(*args):
            if self.controller_type.get() == "Onboard":
                gearingEntry.configure(state="disabled")
                eprEntry.configure(state="disabled")
                hasFollower.configure(state="disabled")
                followerPeriodEntry.configure(state="disabled")
            elif self.controller_type.get() == "Talon":
                gearingEntry.configure(state="normal")
                eprEntry.configure(state="normal")
                hasFollower.configure(state="normal")
                if self.has_follower.get():
                    followerPeriodEntry.configure(state="normal")
                else:
                    followerPeriodEntry.configure(state="disabled")
            else:
                gearingEntry.configure(state="disabled")
                eprEntry.configure(state="disabled")
                hasFollower.configure(state="normal")
                if self.has_follower.get():
                    followerPeriodEntry.configure(state="normal")
                else:
                    followerPeriodEntry.configure(state="disabled")

        def enableUnitsPerRot(*args):
            if not isRotation(self.units.get()) and isRotation(
                self.stored_data["units"]
            ):
                logger.info("Allowing user to modify units per rot")
                diamEntry.configure(state="normal")
                self.units_per_rot.set(0)  # reset the value
            else:
                self.units_per_rot.set(
                    convertUnit(
                        self.stored_data["units"],
                        self.units.get(),
                        self.stored_data["unitsPerRotation"],
                    )
                )
                diamEntry.configure(state="readonly")

        def initialUnitEnable(*args):
            diamEntry.configure(state="normal")
            unitsMenu.configure(state="normal")

        def convertUnit(initUnits, finalUnits, unitsPerRot):
            initUnits = Units(initUnits)
            finalUnits = Units(finalUnits)
            if isRotation(finalUnits):
                logger.info("Converting to rotational measure (fixed conversion)")
                return round(
                    (1 * Units.ROTATIONS.unit).to(finalUnits.unit).magnitude, 3
                )
            else:
                logger.info("Converting from %s to %s measure", initUnits, finalUnits)
                dataUnitsPerRot = unitsPerRot * initUnits.unit
                return round(dataUnitsPerRot.to(finalUnits.unit).magnitude, 3)

        def enableErrorBounds(*args):
            if self.loop_type.get() == "Position":
                qPEntry.configure(state="normal")
            else:
                qPEntry.configure(state="disabled")

        def defineTestResults(*args):
            trackWidthEntry.configure(state="disabled")
            kGEntry.configure(state="disabled")
            kCosEntry.configure(state="disabled")

            test = Tests(self.test.get())
            if test != Tests.DRIVETRAIN:
                dirMenu = OptionMenu(topFrame, self.subset, *sorted(directions))
                self.subset.set("Combined")
            else:
                dirMenu = OptionMenu(topFrame, self.subset, *sorted(subsets))
                self.subset.set("All Combined")
            dirMenu.configure(width=20, state="normal")
            dirMenu.grid(row=0, column=7)
            if test == Tests.DRIVETRAIN or test == Tests.ELEVATOR:
                diamEntry.configure(state="normal")
                if test == Tests.DRIVETRAIN:
                    trackWidthEntry.configure(state="readonly")
                else:
                    kGEntry.configure(state="readonly")
            else:
                diamEntry.configure(state="disabled")
                if test == Tests.ARM:
                    kCosEntry.configure(state="readonly")

        def isRotation(units):
            return Units(units) in (Units.ROTATIONS, Units.RADIANS, Units.DEGREES)

        # TOP OF WINDOW (FILE SELECTION)

        topFrame = Frame(self.mainGUI)
        topFrame.grid(row=0, column=0, columnspan=4)

        Button(topFrame, text="Select Data File", command=getFile).grid(
            row=0, column=0, padx=4
        )

        fileEntry = Entry(topFrame, width=80)
        fileEntry.grid(row=0, column=1, columnspan=3)
        fileEntry.configure(state="readonly")

        Label(topFrame, text="Units per rotation:", anchor="e").grid(
            row=1, column=3, columnspan=2, sticky="ew"
        )
        diamEntry = FloatEntry(topFrame, textvariable=self.units_per_rot)
        diamEntry.grid(row=1, column=5)
        diamEntry.configure(state="disabled")

        Label(topFrame, text="Subset:", width=15).grid(row=0, column=6)
        subsets = {
            "All Combined",
            "Forward Left",
            "Forward Right",
            "Forward Combined",
            "Backward Left",
            "Backward Right",
            "Backward Combined",
        }
        directions = {"Combined", "Forward", "Backward"}
        dirMenu = OptionMenu(topFrame, self.subset, *sorted(directions))
        dirMenu.configure(width=20, state="disabled")
        dirMenu.grid(row=0, column=7)

        Label(topFrame, text="Test:", width=15).grid(row=1, column=6)

        testMenu = FloatEntry(topFrame, textvariable=self.test, width=10)
        testMenu.configure(width=10, state="readonly")
        testMenu.grid(row=1, column=7)
        self.test.trace_add("write", defineTestResults)

        Label(topFrame, text="Units:", width=10).grid(row=0, column=4)

        unitsMenu = OptionMenu(
            topFrame, self.units, *sorted(unit.value for unit in Units)
        )
        unitsMenu.configure(width=10)
        unitsMenu.grid(row=0, column=5, sticky="ew")
        unitsMenu.configure(state="disabled")
        self.units.trace_add("write", enableUnitsPerRot)

        for child in topFrame.winfo_children():
            child.grid_configure(padx=1, pady=1)

        # FEEDFORWARD ANALYSIS FRAME

        ffFrame = Frame(self.mainGUI, bd=2, relief="groove")
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
        windowEntry = IntEntry(ffFrame, textvariable=self.window_size, width=5)
        windowEntry.grid(row=1, column=2)

        Label(ffFrame, text="Motion Threshold (units/s):", anchor="e").grid(
            row=2, column=1, sticky="ew"
        )
        thresholdEntry = FloatEntry(
            ffFrame, textvariable=self.motion_threshold, width=5
        )
        thresholdEntry.grid(row=2, column=2)

        Label(ffFrame, text="kS:", anchor="e").grid(row=1, column=3, sticky="ew")
        kSEntry = FloatEntry(ffFrame, textvariable=self.ks, width=10)
        kSEntry.grid(row=1, column=4)
        kSEntry.configure(state="readonly")

        Label(ffFrame, text="kG:", anchor="e").grid(row=2, column=3, sticky="ew")
        kGEntry = FloatEntry(ffFrame, textvariable=self.kg, width=10)
        kGEntry.grid(row=2, column=4)
        kGEntry.configure(state="disabled")

        Label(ffFrame, text="kCos:", anchor="e").grid(row=3, column=3, sticky="ew")
        kCosEntry = FloatEntry(ffFrame, textvariable=self.kcos, width=10)
        kCosEntry.grid(row=3, column=4)
        kCosEntry.configure(state="disabled")

        Label(ffFrame, text="kV:", anchor="e").grid(row=4, column=3, sticky="ew")
        kVEntry = FloatEntry(ffFrame, textvariable=self.kv, width=10)
        kVEntry.grid(row=4, column=4)
        kVEntry.configure(state="readonly")

        Label(ffFrame, text="kA:", anchor="e").grid(row=5, column=3, sticky="ew")
        kAEntry = FloatEntry(ffFrame, textvariable=self.ka, width=10)
        kAEntry.grid(row=5, column=4)
        kAEntry.configure(state="readonly")

        Label(ffFrame, text="r-squared:", anchor="e").grid(row=6, column=3, sticky="ew")
        rSquareEntry = FloatEntry(ffFrame, textvariable=self.r_square, width=10)
        rSquareEntry.grid(row=6, column=4)
        rSquareEntry.configure(state="readonly")

        Label(ffFrame, text="Track Width:", anchor="e").grid(
            row=7, column=3, sticky="ew"
        )
        trackWidthEntry = FloatEntry(ffFrame, textvariable=self.track_width, width=10)
        trackWidthEntry.grid(row=7, column=4)
        trackWidthEntry.configure(state="disabled")

        for child in ffFrame.winfo_children():
            child.grid_configure(padx=1, pady=1)

        # FEEDBACK ANALYSIS FRAME

        fbFrame = Frame(self.mainGUI, bd=2, relief="groove")
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
        presetMenu = OptionMenu(fbFrame, self.gain_units_preset, *sorted(presetChoices))
        presetMenu.grid(row=1, column=1)
        presetMenu.config(width=12)
        self.gain_units_preset.trace_add("write", presetGains)

        Label(fbFrame, text="Controller Period (s):", anchor="e").grid(
            row=2, column=0, sticky="ew"
        )
        periodEntry = FloatEntry(fbFrame, textvariable=self.period, width=10)
        periodEntry.grid(row=2, column=1)

        Label(fbFrame, text="Max Controller Output:", anchor="e").grid(
            row=3, column=0, sticky="ew"
        )
        controllerMaxEntry = FloatEntry(
            fbFrame, textvariable=self.max_controller_output, width=10
        )
        controllerMaxEntry.grid(row=3, column=1)

        Label(fbFrame, text="Time-Normalized Controller:", anchor="e").grid(
            row=4, column=0, sticky="ew"
        )
        normalizedButton = Checkbutton(
            fbFrame, variable=self.controller_time_normalized
        )
        normalizedButton.grid(row=4, column=1)

        Label(fbFrame, text="Controller Type:", anchor="e").grid(
            row=5, column=0, sticky="ew"
        )
        controllerTypes = {"Onboard", "Talon", "Spark"}
        controllerTypeMenu = OptionMenu(
            fbFrame, self.controller_type, *sorted(controllerTypes)
        )
        controllerTypeMenu.grid(row=5, column=1)
        self.controller_type.trace_add("write", enableOffboard)

        Label(fbFrame, text="Measurement delay (ms):", anchor="e").grid(
            row=6, column=0, sticky="ew"
        )
        velocityDelay = FloatEntry(
            fbFrame, textvariable=self.measurement_delay, width=10
        )
        velocityDelay.grid(row=6, column=1)

        Label(fbFrame, text="Post-Encoder Gearing:", anchor="e").grid(
            row=7, column=0, sticky="ew"
        )
        gearingEntry = FloatEntry(fbFrame, textvariable=self.gearing, width=10)
        gearingEntry.configure(state="disabled")
        gearingEntry.grid(row=7, column=1)

        Label(fbFrame, text="Encoder EPR:", anchor="e").grid(
            row=8, column=0, sticky="ew"
        )
        eprEntry = IntEntry(fbFrame, textvariable=self.encoder_epr, width=10)
        eprEntry.configure(state="disabled")
        eprEntry.grid(row=8, column=1)

        Label(fbFrame, text="Has Follower:", anchor="e").grid(
            row=9, column=0, sticky="ew"
        )
        hasFollower = Checkbutton(fbFrame, variable=self.has_follower)
        hasFollower.grid(row=9, column=1)
        hasFollower.configure(state="disabled")
        self.has_follower.trace_add("write", enableOffboard)

        Label(fbFrame, text="Follower Update Period (s):", anchor="e").grid(
            row=10, column=0, sticky="ew"
        )
        followerPeriodEntry = FloatEntry(
            fbFrame, textvariable=self.follower_period, width=10
        )
        followerPeriodEntry.grid(row=10, column=1)
        followerPeriodEntry.configure(state="disabled")

        Label(fbFrame, text="Max Acceptable Position Error (units):", anchor="e").grid(
            row=1, column=2, columnspan=2, sticky="ew"
        )
        qPEntry = FloatEntry(fbFrame, textvariable=self.qp, width=10)
        qPEntry.grid(row=1, column=4)
        qPEntry.configure(state="disabled")

        Label(
            fbFrame, text="Max Acceptable Velocity Error (units/s):", anchor="e"
        ).grid(row=2, column=2, columnspan=2, sticky="ew")
        qVEntry = FloatEntry(fbFrame, textvariable=self.qv, width=10)
        qVEntry.grid(row=2, column=4)

        Label(fbFrame, text="Max Acceptable Control Effort (V):", anchor="e").grid(
            row=3, column=2, columnspan=2, sticky="ew"
        )
        effortEntry = FloatEntry(fbFrame, textvariable=self.max_effort, width=10)
        effortEntry.grid(row=3, column=4)

        Label(fbFrame, text="Loop Type:", anchor="e").grid(
            row=4, column=2, columnspan=2, sticky="ew"
        )
        loopTypes = {"Position", "Velocity"}
        loopTypeMenu = OptionMenu(fbFrame, self.loop_type, *sorted(loopTypes))
        loopTypeMenu.configure(width=8)
        loopTypeMenu.grid(row=4, column=4)
        self.loop_type.trace_add("write", enableErrorBounds)
        # We reset everything to the selected preset when the user changes the loop type
        # This prevents people from forgetting to change measurement delays
        self.loop_type.trace_add("write", presetGains)

        Label(fbFrame, text="kV:", anchor="e").grid(row=5, column=2, sticky="ew")
        kVFBEntry = FloatEntry(fbFrame, textvariable=self.kv, width=10)
        kVFBEntry.grid(row=5, column=3)
        Label(fbFrame, text="kA:", anchor="e").grid(row=6, column=2, sticky="ew")
        kAFBEntry = FloatEntry(fbFrame, textvariable=self.ka, width=10)
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
            fbFrame, textvariable=self.kp, width=10, state="readonly"
        ).grid(row=8, column=3)

        Label(fbFrame, text="kD:", anchor="e").grid(row=9, column=2, sticky="ew")
        kDEntry = FloatEntry(
            fbFrame, textvariable=self.kd, width=10, state="readonly"
        ).grid(row=9, column=3)

        Label(fbFrame, text="Convert Gains:", anchor="e").grid(
            row=8, column=4, sticky="ew"
        )
        convertGains = Checkbutton(fbFrame, variable=self.convert_gains)
        convertGains.grid(row=8, column=5)
        convertGains.configure(state="disabled")

        for child in fbFrame.winfo_children():
            child.grid_configure(padx=1, pady=1)

    # From 449's R script (note: R is 1-indexed)

    def smoothDerivative(self, tm, value, n):
        """
        :param tm: time column
        :param value: Value to take the derivative of
        :param n: smoothing parameter
        """
        dlen = len(value)
        dt = tm[n:dlen] - tm[: (dlen - n)]
        x = (value[(n):dlen] - value[: (dlen - n)]) / dt

        # pad to original length by adding zeros on either side
        return np.pad(
            x, (int(np.ceil(n / 2.0)), int(np.floor(n / 2.0))), mode="constant"
        )

    # Create one for one sided and one for 2 sided
    def trim_quasi_testdata(self, data):
        adata = np.abs(data)
        test = Tests(self.test.get())
        if test == Tests.DRIVETRAIN:
            truth = np.all(
                [
                    adata[L_ENCODER_V_COL] > self.motion_threshold.get(),
                    adata[L_VOLTS_COL] > 0,
                    adata[R_ENCODER_V_COL] > self.motion_threshold.get(),
                    adata[R_VOLTS_COL] > 0,
                ],
                axis=0,
            )
        else:
            truth = np.all(
                [
                    adata[L_ENCODER_V_COL] > self.motion_threshold.get(),
                    adata[L_VOLTS_COL] > 0,
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

    def trim_step_testdata(self, data):
        # removes anything before the max acceleration
        max_accel_idx = np.argmax(np.abs(data[PREPARED_ACC_COL]))
        return data[:, max_accel_idx + 1 :]

    def compute_accelDrive(self, data, window):
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
        l_acc = self.smoothDerivative(data[TIME_COL], data[L_ENCODER_V_COL], window)
        r_acc = self.smoothDerivative(data[TIME_COL], data[R_ENCODER_V_COL], window)

        l = np.vstack(
            (
                data[TIME_COL],
                data[L_VOLTS_COL],
                data[L_ENCODER_P_COL],
                data[L_ENCODER_V_COL],
                l_acc,
            )
        )
        r = np.vstack(
            (
                data[TIME_COL],
                data[R_VOLTS_COL],
                data[R_ENCODER_P_COL],
                data[R_ENCODER_V_COL],
                r_acc,
            )
        )

        return l, r

    def compute_accel(self, data, window):
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
        acc = self.smoothDerivative(data[TIME_COL], data[L_ENCODER_V_COL], window)

        dat = np.vstack(
            (
                data[TIME_COL],
                data[L_VOLTS_COL],
                data[L_ENCODER_P_COL],
                data[L_ENCODER_V_COL],
                acc,
            )
        )

        return dat

    def is_valid(self, *a_tuple):
        for a in a_tuple:
            if a is None:
                return False
        return True

    def prepare_data_drivetrain(self, data, window):
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
        # ensure voltage sign matches velocity sign and converts rotation measurements into proper units
        for x in JSON_DATA_KEYS:
            data[x][L_VOLTS_COL] = np.copysign(
                data[x][L_VOLTS_COL], data[x][L_ENCODER_V_COL]
            )
            data[x][R_VOLTS_COL] = np.copysign(
                data[x][R_VOLTS_COL], data[x][R_ENCODER_V_COL]
            )
            data[x][R_ENCODER_V_COL] = (
                np.array(data[x][R_ENCODER_V_COL]) * self.units_per_rot.get()
            ).tolist()
            data[x][L_ENCODER_V_COL] = (
                np.array(data[x][L_ENCODER_V_COL]) * self.units_per_rot.get()
            ).tolist()
            data[x][R_ENCODER_P_COL] = (
                np.array(data[x][R_ENCODER_V_COL]) * self.units_per_rot.get()
            ).tolist()
            data[x][L_ENCODER_P_COL] = (
                np.array(data[x][L_ENCODER_V_COL]) * self.units_per_rot.get()
            ).tolist()

        # trim quasi data before computing acceleration
        sf_trim = self.trim_quasi_testdata(data["slow-forward"])
        sb_trim = self.trim_quasi_testdata(data["slow-backward"])

        if sf_trim is None or sb_trim is None:
            return [None] * 8

        sf_l, sf_r = self.compute_accelDrive(sf_trim, window)
        sb_l, sb_r = self.compute_accelDrive(sb_trim, window)

        if sf_l is None or sf_r is None or sb_l is None or sb_r is None:
            return [None] * 8

        # trim step data after computing acceleration
        ff_l, ff_r = self.compute_accelDrive(data["fast-forward"], window)
        fb_l, fb_r = self.compute_accelDrive(data["fast-backward"], window)

        if ff_l is None or ff_r is None or fb_l is None or fb_r is None:
            return [None] * 8

        ff_l = self.trim_step_testdata(ff_l)
        ff_r = self.trim_step_testdata(ff_r)
        fb_l = self.trim_step_testdata(fb_l)
        fb_r = self.trim_step_testdata(fb_r)

        dataset = {
            "Forward Left": [sf_l, ff_l],
            "Forward Right": [sf_r, ff_r],
            "Backward Left": [sb_l, fb_l],
            "Backward Right": [sb_r, fb_r],
            "Forward Combined": [
                np.concatenate((sf_l, sf_r), axis=1),
                np.concatenate((ff_l, ff_r), axis=1),
            ],
            "Backward Combined": [
                np.concatenate((sb_l, sb_r), axis=1),
                np.concatenate((fb_l, fb_r), axis=1),
            ],
            "All Combined": [
                np.concatenate((sf_l, sb_l, sf_r, sb_r), axis=1),
                np.concatenate((ff_l, fb_l, ff_r, ff_r), axis=1),
            ],
            "Valid": self.is_valid(sf_l, sb_l, ff_l, fb_l, sf_r, sb_r, ff_r, fb_r),
        }

        return dataset

    def prepare_data(self, ogData, window):
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
        # create a copy so original data doesn't get changed
        data = copy.deepcopy(ogData)

        test = Tests(self.test.get())
        if test == Tests.DRIVETRAIN:
            return self.prepare_data_drivetrain(data, window)
        else:
            # Ensure voltage points in same direction as velocity
            for x in JSON_DATA_KEYS:
                data[x][L_VOLTS_COL] = np.copysign(
                    data[x][L_VOLTS_COL], data[x][L_ENCODER_V_COL]
                )
                data[x][L_ENCODER_V_COL] = (
                    np.array(data[x][L_ENCODER_V_COL]) * self.units_per_rot.get()
                ).tolist()
                data[x][L_ENCODER_P_COL] = (
                    np.array(data[x][L_ENCODER_V_COL]) * self.units_per_rot.get()
                ).tolist()

            # trim quasi data before computing acceleration
            sf_trim = self.trim_quasi_testdata(data["slow-forward"])
            sb_trim = self.trim_quasi_testdata(data["slow-backward"])

            if sf_trim is None or sb_trim is None:
                return None, None, None, None

            sf = self.compute_accel(sf_trim, window)
            sb = self.compute_accel(sb_trim, window)

            if sf is None or sb is None:
                return None, None, None, None

            # trim step data after computing acceleration
            ff = self.compute_accel(data["fast-forward"], window)
            fb = self.compute_accel(data["fast-backward"], window)

            if ff is None or fb is None:
                return None, None, None, None

            ff = self.trim_step_testdata(ff)
            fb = self.trim_step_testdata(fb)

            dataset = {
                "Forward": [sf, ff],
                "Backward": [sb, fb],
                "Combined": [
                    np.concatenate((sf, sb), axis=1),
                    np.concatenate((ff, fb), axis=1),
                ],
                "Valid": self.is_valid(sf, sb, ff, fb),
            }
            return dataset

    def ols(self, x1, x2, x3, y):
        """multivariate linear regression using ordinary least squares"""
        if x3:
            x = np.array((np.sign(x1), x1, x2, x3)).T
        else:
            x = np.array((np.sign(x1), x1, x2)).T
        model = sm.OLS(y, x)
        return model.fit()

    def _plotTimeDomain(self, subset, qu, step):
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
        plt.scatter(
            step[PREPARED_TM_COL], step[PREPARED_VEL_COL], marker=".", c="#000000"
        )

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
        plt.scatter(
            step[PREPARED_TM_COL], step[PREPARED_ACC_COL], marker=".", c="#000000"
        )

        # Fix overlapping axis labels
        plt.tight_layout(pad=0.5)

        plt.show()

    def _plotVoltageDomain(self, subset, qu, step):

        # Voltage-domain plots
        # These should show linearity of velocity/acceleration data with voltage
        # X-axis is not raw voltage, but rather 'portion of voltage corresponding to vel/acc'
        # Both plots should be straight lines through the origin
        # Fit lines will be straight lines through the origin by construction; data should match fit

        vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
        accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
        volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
        time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

        ks = self.ks.get()
        kv = self.kv.get()
        ka = self.ka.get()
        r_square = self.r_square.get()

        kcos = self.kcos.get()
        kg = self.kg.get()

        plt.figure(subset + " Voltage-Domain Plots")

        # quasistatic vel vs. vel-causing voltage
        ax = plt.subplot(211)
        ax.set_xlabel("Velocity-Portion Voltage")
        ax.set_ylabel("Velocity")
        ax.set_title("Quasistatic velocity vs velocity-portion voltage")

        test = Tests(self.test.get())
        if test == Tests.ELEVATOR:
            plt.scatter(
                qu[PREPARED_V_COL]
                - kg
                - ks * np.sign(qu[PREPARED_VEL_COL])
                - ka * qu[PREPARED_ACC_COL],
                qu[PREPARED_VEL_COL],
                marker=".",
                c="#000000",
            )
        elif test == Tests.ARM:
            plt.scatter(
                qu[PREPARED_V_COL]
                - ks * np.sign(qu[PREPARED_VEL_COL])
                - ka * qu[PREPARED_ACC_COL]
                - kcos * qu[PREPARED_COS_COL],
                qu[PREPARED_VEL_COL],
                marker=".",
                c="#000000",
            )
        else:
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

        if test == Tests.ELEVATOR:
            plt.scatter(
                step[PREPARED_V_COL]
                - kg
                - ks * np.sign(step[PREPARED_VEL_COL])
                - kv * step[PREPARED_VEL_COL],
                step[PREPARED_ACC_COL],
                marker=".",
                c="#000000",
            )
        elif test == Tests.ARM:
            plt.scatter(
                step[PREPARED_V_COL]
                - ks * np.sign(step[PREPARED_VEL_COL])
                - kv * step[PREPARED_VEL_COL]
                - kcos * step[PREPARED_COS_COL],
                step[PREPARED_ACC_COL],
                marker=".",
                c="#000000",
            )
        else:
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

        # Supplemental graphs (Elevator and Arm)
        if test == Tests.ELEVATOR or test == Tests.ARM:
            ax = plt.subplot(111)
            # show fit line from multiple regression
            y = np.linspace(np.min(qu[PREPARED_POS_COL]), np.max(qu[PREPARED_POS_COL]))

            if test == Tests.ELEVATOR:
                ax.set_xlabel("Friction-loss voltage")
                ax.set_ylabel("Velocity")
                ax.set_title("Quasistatic velocity vs friction-loss voltage")
                plt.scatter(
                    qu[PREPARED_V_COL]
                    - kg
                    - kv * qu[PREPARED_VEL_COL]
                    - ka * qu[PREPARED_ACC_COL],
                    qu[PREPARED_VEL_COL],
                    marker=".",
                    c="#000000",
                )
                plt.plot(ks * np.sign(y), y)
            else:
                ax.set_xlabel("Gravity (cosine)-Portion Voltage")
                ax.set_ylabel("Angle")
                ax.set_title("Quasistatic angle vs gravity-portion voltage")
                plt.scatter(
                    qu[PREPARED_V_COL]
                    - ks * np.sign(qu[PREPARED_VEL_COL])
                    - kv * qu[PREPARED_VEL_COL]
                    - ka * qu[PREPARED_ACC_COL],
                    qu[PREPARED_POS_COL],
                    marker=".",
                    c="#000000",
                )
                units = Units(self.units.get())
                if units == Units.DEGREES:
                    plt.plot(kcos * np.cos(np.radians(y)), y)
                elif units == Units.RADIANS:
                    plt.plot(kcos * np.cos(y), y)
                else:
                    plt.plot(kcos * np.cos(math.pi * 2 * y), y)
            plt.tight_layout(pad=0.5)

        plt.show()

    def _plot3D(self, subset, qu, step):

        vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
        accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
        volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
        time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

        ks = self.ks.get()
        kv = self.kv.get()
        ka = self.ka.get()
        kcos = self.kcos.get()
        kg = self.kg.get()
        r_square = self.r_square.get()

        # Interactive 3d plot of voltage over entire vel-accel plane
        # Really cool, not really any more diagnostically-useful than prior plots but worth seeing
        plt.figure(subset + " 3D Vel-Accel Plane Plot")

        ax = plt.subplot(111, projection="3d")

        # 3D scatterplot
        ax.set_xlabel("Velocity")
        ax.set_ylabel("Acceleration")
        ax.set_zlabel("Voltage")

        # Show best fit plane
        vv, aa = np.meshgrid(
            np.linspace(np.min(vel), np.max(vel)),
            np.linspace(np.min(accel), np.max(accel)),
        )

        test = Tests(self.test.get())
        if test == Tests.ELEVATOR:
            ax.set_title("Friction-adjusted Voltage vs velocity and acceleration")
            ax.scatter(vel, accel, volts - ks * np.sign(vel))
            ax.plot_surface(vv, aa, kg + kv * vv + ka * aa, alpha=0.2, color=[0, 1, 1])
        elif test == Tests.ARM:
            cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
            ax.set_title("Cosine-adjusted Voltage vs velocity and acceleration")
            ax.scatter(vel, accel, volts - kcos * cos)
            ax.plot_surface(
                vv, aa, ks * np.sign(vv) + kv * vv + ka * aa, alpha=0.2, color=[0, 1, 1]
            )
        else:
            ax.set_title("Voltage vs velocity and acceleration")
            ax.scatter(vel, accel, volts)
            ax.plot_surface(
                vv, aa, ks * np.sign(vv) + kv * vv + ka * aa, alpha=0.2, color=[0, 1, 1]
            )

        plt.show()

    def calcFit(self, qu, step, test):
        vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
        accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
        volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
        time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

        test = Tests(test)
        if test == Tests.ELEVATOR:
            fit = self.ols(vel, accel, np.ones(vel.size), volts)
            ks, kv, ka, kg = fit.params
            rsquare = fit.rsquared
            return kg, ks, kv, ka, rsquare
        elif test == Tests.ARM:
            cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
            fit = self.ols(vel, accel, cos, volts)
            ks, kv, ka, kcos = fit.params
            rsquare = fit.rsquared
            return ks, kv, ka, kcos, rsquare
        else:
            fit = self.ols(vel, accel, None, volts)
            ks, kv, ka = fit.params
            rsquare = fit.rsquared
        return ks, kv, ka, rsquare

    def _calcGainsPos(self, kv, ka, qp, qv, effort, period, position_delay):

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

    def _calcGainsVel(self, kv, ka, qv, effort, period, velocity_delay):

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

    analyzer = Analyzer(dir)

    analyzer.mainGUI.title("FRC Drive Characterization Tool")

    analyzer.configure_gui()
    analyzer.mainGUI.mainloop()


if __name__ == "__main__":
    main(os.getcwd())
