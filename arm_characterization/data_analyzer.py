#!/usr/bin/env python3
#
# This analyzes the data collected by the data_logger.py script. It is ran
# automatically after the data_logger.py script is ran, but you can also
# invoke it separately and give it JSON data to analyze.
#
# The analysis and data cleanup is carried out in accordance with the
# specification at https://www.chiefdelphi.com/forums/showthread.php?t=161539
#

import argparse
import csv
import json
import math
import tkinter
from tkinter import *
from tkinter import filedialog
from os.path import basename, exists, dirname, join, splitext

import control as cnt
import frccontrol as frccnt
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from mpl_toolkits.mplot3d import Axes3D


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


mainGUI = None

STATE = None

#
# These parameters are used to indicate which column of data each parameter
# can be found at
#

columns = dict(
    time=0,
    battery=1,
    autospeed=2,
    volts=3,
    encoder_pos=4,
    encoder_vel=5,
)


class ProgramState:
    def __init__(self):
        # Set fields
        self.window_size = IntVar(mainGUI)
        self.motion_threshold = DoubleVar(mainGUI)
        self.direction = StringVar(mainGUI)

        self.units = StringVar(mainGUI)

        self.stored_data = None

        self.quasi_forward = None
        self.quasi_backward = None
        self.step_forward = None
        self.step_backward = None

        self.ks = DoubleVar(mainGUI)
        self.kv = DoubleVar(mainGUI)
        self.ka = DoubleVar(mainGUI)
        self.kcos = DoubleVar(mainGUI)
        self.r_square = DoubleVar(mainGUI)

        self.qp = DoubleVar(mainGUI)
        self.qv = DoubleVar(mainGUI)
        self.max_effort = DoubleVar(mainGUI)
        self.period = DoubleVar(mainGUI)
        self.max_controller_output = DoubleVar(mainGUI)
        self.controller_time_normalized = BooleanVar(mainGUI)

        self.gearing = DoubleVar(mainGUI)

        self.controller_type = StringVar(mainGUI)
        self.encoder_ppr = IntVar(mainGUI)
        self.has_slave = BooleanVar(mainGUI)
        self.slave_period = DoubleVar(mainGUI)

        self.gain_units_preset = StringVar(mainGUI)

        self.kp = DoubleVar(mainGUI)
        self.kd = DoubleVar(mainGUI)


        # Set field defaults
        self.window_size.set(8)
        self.motion_threshold.set(20)
        self.direction.set('Combined')

        self.units.set('Degrees')

        self.ks.set(0)
        self.kv.set(0)
        self.ka.set(0)
        self.kcos.set(0)
        self.r_square.set(0)

        self.qp.set(2)
        self.qv.set(4)
        self.max_effort.set(7)
        self.period.set(.02)
        self.max_controller_output.set(12)
        self.controller_time_normalized.set(True)

        self.gearing.set(1)

        self.controller_type.set("Onboard")
        self.encoder_ppr.set(4096)
        self.has_slave.set(False)
        self.slave_period.set(.01)

        self.gain_units_preset.set('Default')

        self.kp.set(0)
        self.kd.set(0)


# Set up main window

def configure_gui():

    def getFile():
        dataFile = tkinter.filedialog.askopenfile(
            parent=mainGUI, mode='rb', title='Choose the data file (.JSON)')
        fileEntry.configure(state='normal')
        fileEntry.delete(0, END)
        fileEntry.insert(0, dataFile.name)
        fileEntry.configure(state='readonly')

        data = json.load(dataFile)

        # Transform the data into a numpy array to make it easier to use
        # -> transpose it so we can deal with it in columns
        for k in JSON_DATA_KEYS:
            data[k] = np.array(data[k]).transpose()

        STATE.stored_data = data

        analyzeButton.configure(state='normal')

    def runAnalysis():

        STATE.quasi_forward, STATE.quasi_backward, STATE.step_forward, STATE.step_backward = prepare_data(
            STATE.stored_data, window=STATE.window_size.get())

        if (STATE.quasi_forward is None
            or STATE.quasi_backward is None
            or STATE.step_forward is None
                or STATE.step_backward is None):
            return

        if STATE.direction.get() == 'Forward':
            ks, kv, ka, kcos, rsquare = calcFit(
                STATE.quasi_forward, STATE.step_forward)
        elif STATE.direction.get() == 'Backward':
            ks, kv, ka, kcos, rsquare = calcFit(
                STATE.quasi_backward, STATE.step_backward)
        else:
            ks, kv, ka, kcos, rsquare = calcFit(
                np.concatenate(
                    (STATE.quasi_forward, STATE.quasi_backward), axis=1),
                np.concatenate((STATE.step_forward, STATE.step_backward), axis=1))

        STATE.ks.set('%s' % float('%.3g' % ks))
        STATE.kv.set('%s' % float('%.3g' % kv))
        STATE.ka.set('%s' % float('%.3g' % ka))
        STATE.kcos.set('%s' % float('%.3g' % kcos))
        STATE.r_square.set('%s' % float('%.3g' % rsquare))

        calcGains()

        timePlotsButton.configure(state='normal')
        voltPlotsButton.configure(state='normal')
        fancyPlotButton.configure(state='normal')
        calcGainsButton.configure(state='normal')

    def plotTimeDomain():
        if STATE.direction.get() == 'Forward':
            _plotTimeDomain('Forward', STATE.quasi_forward, STATE.step_forward)
        elif STATE.direction.get() == 'Backward':
            _plotTimeDomain('Backward', STATE.quasi_backward,
                            STATE.step_backward)
        else:
            _plotTimeDomain('Combined',
                            np.concatenate(
                                (STATE.quasi_forward, STATE.quasi_backward), axis=1),
                            np.concatenate((STATE.step_forward, STATE.step_backward), axis=1))

    def plotVoltageDomain():
        if STATE.direction.get() == 'Forward':
            _plotVoltageDomain(
                'Forward', STATE.quasi_forward, STATE.step_forward)
        elif STATE.direction.get() == 'Backward':
            _plotVoltageDomain(
                'Backward', STATE.quasi_backward, STATE.step_backward)
        else:
            _plotVoltageDomain('Combined',
                               np.concatenate(
                                   (STATE.quasi_forward, STATE.quasi_backward), axis=1),
                               np.concatenate((STATE.step_forward, STATE.step_backward), axis=1))

    def plot3D():
        if STATE.direction.get() == 'Forward':
            _plot3D('Forward', STATE.quasi_forward, STATE.step_forward)
        elif STATE.direction.get() == 'Backward':
            _plot3D('Backward', STATE.quasi_backward, STATE.step_backward)
        else:
            _plot3D('Combined',
                    np.concatenate(
                        (STATE.quasi_forward, STATE.quasi_backward), axis=1),
                    np.concatenate((STATE.step_forward, STATE.step_backward), axis=1))

    def calcGains():

        period = STATE.period.get() if not STATE.has_slave.get() else STATE.slave_period.get()

        kp, kd = _calcGains(
            STATE.kv.get(),
            STATE.ka.get(),
            STATE.qp.get(),
            STATE.qv.get(),
            STATE.max_effort.get(),
            period)

        # Scale gains to output
        kp = kp / 12 * STATE.max_controller_output.get()
        kd = kd / 12 * STATE.max_controller_output.get()

        # Rescale kD if not time-normalized
        if not STATE.controller_time_normalized.get():
            kd = kd/STATE.period.get()

        # Get correct conversion factor for rotations
        if STATE.units.get() == 'Degrees':
            rotation = 360
        elif STATE.units.get() == 'Radians':
            rotation = 2*math.pi
        elif STATE.units.get() == 'Rotations':
            rotation = 1

        # Scale by gearing if using Talon
        if STATE.controller_type.get() == 'Talon':
            kp = kp * rotation / (STATE.encoder_ppr.get() * STATE.gearing.get())
            kd = kd * rotation / (STATE.encoder_ppr.get() * STATE.gearing.get())

        STATE.kp.set('%s' % float('%.3g' % kp))
        STATE.kd.set('%s' % float('%.3g' % kd))

    def presetGains(*args):

        presets = {
            'Default': lambda: (
                STATE.max_controller_output.set(12),
                STATE.period.set(.02),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set('Onboard')),
            'WPILib (new)': lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(.02),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set('Onboard')),
            'WPILib (old)': lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(.05),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set('Onboard')),
            'Talon (new)': lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(.001),
                STATE.controller_time_normalized.set(True),
                STATE.controller_type.set('Talon')),
            'Talon (old)': lambda: (
                STATE.max_controller_output.set(1023),
                STATE.period.set(.001),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set('Talon')),
            'Spark MAX': lambda: (
                STATE.max_controller_output.set(1),
                STATE.period.set(.001),
                STATE.controller_time_normalized.set(False),
                STATE.controller_type.set('Spark')),
        }

        presets.get(STATE.gain_units_preset.get(), "Default")()

    def enableOffboard(*args):
        if STATE.controller_type.get() == 'Onboard':
            gearingEntry.configure(state='disabled')
            pprEntry.configure(state='disabled')
            hasSlave.configure(state='disabled')
            slavePeriodEntry.configure(state='disabled')
        elif STATE.controller_type.get() == 'Talon':
            gearingEntry.configure(state='normal')
            pprEntry.configure(state='normal')
            hasSlave.configure(state='normal')
            if STATE.has_slave.get():
                slavePeriodEntry.configure(state='normal')
            else:
                slavePeriodEntry.configure(state='disabled')
        else:
            gearingEntry.configure(state='disabled')
            pprEntry.configure(state='disabled')
            hasSlave.configure(state='normal')
            if STATE.has_slave.get():
                slavePeriodEntry.configure(state='normal')
            else:
                slavePeriodEntry.configure(state='disabled')

    def validateInt(P):
        if str.isdigit(P) or P == "":
            return True
        else:
            return False

    def validateFloat(P):
        if isfloat(P) or P == "":
            return True
        else:
            return False

    valInt = mainGUI.register(validateInt)
    valFloat = mainGUI.register(validateFloat)

    # TOP OF WINDOW (FILE SELECTION)

    Button(mainGUI, text="Select Data File",
           command=getFile).grid(row=0, column=0)

    fileEntry = Entry(mainGUI, width=90)
    fileEntry.grid(row=0, column=1, columnspan=3)
    fileEntry.configure(state='readonly')

    Label(mainGUI, text='Units:', width=10).grid(row=0, column=4)

    unitChoices = {'Degrees', 'Radians', 'Rotations'}
    unitsMenu = OptionMenu(mainGUI, STATE.units, *sorted(unitChoices))
    unitsMenu.configure(width=10)
    unitsMenu.grid(row=0, column=5, sticky='ew')

    Label(mainGUI, text='Direction:', width=10).grid(row=0, column=6)
    directions = {'Combined', 'Forward', 'Backward'}

    dirMenu = OptionMenu(mainGUI, STATE.direction, *sorted(directions))
    dirMenu.configure(width=10)
    dirMenu.grid(row=0, column=7)

    # FEEDFORWARD ANALYSIS FRAME

    ffFrame = Frame(mainGUI, bd=2, relief='groove')
    ffFrame.grid(row=1, column=0, columnspan=3, sticky='ns')

    Label(ffFrame, text="Feedforward Analysis").grid(
        row=0, column=0, columnspan=5)

    analyzeButton = Button(ffFrame, text="Analyze Data",
                           command=runAnalysis, state='disabled')
    analyzeButton.grid(row=1, column=0, sticky='ew')

    timePlotsButton = Button(ffFrame, text="Time-Domain Diagnostics",
                             command=plotTimeDomain, state='disabled')
    timePlotsButton.grid(row=2, column=0, sticky='ew')

    voltPlotsButton = Button(ffFrame, text="Voltage-Domain Diagnostics",
                             command=plotVoltageDomain, state='disabled')
    voltPlotsButton.grid(row=3, column=0, sticky='ew')

    fancyPlotButton = Button(ffFrame, text="3D Diagnostics",
                             command=plot3D, state='disabled')
    fancyPlotButton.grid(row=4, column=0, sticky='ew')

    Label(ffFrame, text='Accel Window Size:', anchor='e').grid(
        row=1, column=1, sticky='ew')
    windowEntry = Entry(ffFrame, textvariable=STATE.window_size,
                        width=5, validate='all', validatecommand=(valInt, '%P'))
    windowEntry.grid(row=1, column=2)

    Label(ffFrame, text='Motion Threshold (units/s):',
          anchor='e').grid(row=2, column=1, sticky='ew')
    thresholdEntry = Entry(ffFrame, textvariable=STATE.motion_threshold,
                           width=5, validate='all', validatecommand=(valFloat, '%P'))
    thresholdEntry.grid(row=2, column=2)

    Label(ffFrame, text='kS:', anchor='e').grid(row=1, column=3, sticky='ew')
    kSEntry = Entry(ffFrame, textvariable=STATE.ks, width=10)
    kSEntry.grid(row=1, column=4)
    kSEntry.configure(state='readonly')

    Label(ffFrame, text='kV:', anchor='e').grid(row=2, column=3, sticky='ew')
    kVEntry = Entry(ffFrame, textvariable=STATE.kv, width=10)
    kVEntry.grid(row=2, column=4)
    kVEntry.configure(state='readonly')

    Label(ffFrame, text='kA:', anchor='e').grid(row=3, column=3, sticky='ew')
    kAEntry = Entry(ffFrame, textvariable=STATE.ka, width=10)
    kAEntry.grid(row=3, column=4)
    kAEntry.configure(state='readonly')

    Label(ffFrame, text='kCos:', anchor='e').grid(row=4, column=3, sticky='ew')
    kCosEntry = Entry(ffFrame, textvariable=STATE.kcos, width=10)
    kCosEntry.grid(row=4, column=4)
    kCosEntry.configure(state='readonly')

    Label(ffFrame, text='r-squared:',
          anchor='e').grid(row=5, column=3, sticky='ew')
    rSquareEntry = Entry(ffFrame, textvariable=STATE.r_square, width=10)
    rSquareEntry.grid(row=5, column=4)
    rSquareEntry.configure(state='readonly')

    # FEEDBACK ANALYSIS FRAME

    fbFrame = Frame(mainGUI, bd=2, relief='groove')
    fbFrame.grid(row=1, column=3, columnspan=5)

    Label(fbFrame, text='Feedback Analysis').grid(
        row=0, column=0, columnspan=5)

    Label(fbFrame, text='Gain Settings Preset:',
          anchor='e').grid(row=1, column=0, sticky='ew')
    presetChoices = {
        'Default', 'WPILib (new)', 'WPILib (old)', 'Talon (new)', 'Talon (old)', 'Spark MAX'}
    presetMenu = OptionMenu(
        fbFrame, STATE.gain_units_preset, *sorted(presetChoices))
    presetMenu.grid(row=1, column=1)
    presetMenu.config(width=12)
    STATE.gain_units_preset.trace_add('write', presetGains)

    Label(fbFrame, text='Controller Period (s):',
          anchor='e').grid(row=2, column=0, sticky='ew')
    periodEntry = Entry(fbFrame, textvariable=STATE.period, width=10,
                        validate='all', validatecommand=(valFloat, '%P'))
    periodEntry.grid(row=2, column=1)

    Label(fbFrame, text='Max Controller Output:',
          anchor='e').grid(row=3, column=0, sticky='ew')
    controllerMaxEntry = Entry(fbFrame, textvariable=STATE.max_controller_output, width=10,
                               validate='all', validatecommand=(valFloat, '%P'))
    controllerMaxEntry.grid(row=3, column=1)

    Label(fbFrame, text='Time-Normalized Controller:',
          anchor='e').grid(row=4, column=0, sticky='ew')
    normalizedButton = Checkbutton(
        fbFrame, variable=STATE.controller_time_normalized)
    normalizedButton.grid(row=4, column=1)

    Label(fbFrame, text='Controller Type:', anchor='e').grid(
        row=5, column=0, sticky='ew')
    controllerTypes = {'Onboard', 'Talon', 'Spark'}
    controllerTypeMenu = OptionMenu(
        fbFrame, STATE.controller_type, *sorted(controllerTypes))
    controllerTypeMenu.grid(row=5, column=1)
    STATE.controller_type.trace_add('write', enableOffboard)

    Label(fbFrame, text='Post-Encoder Gearing:',
          anchor='e').grid(row=6, column=0, sticky='ew')
    gearingEntry = Entry(fbFrame, textvariable=STATE.gearing, width=10,
                         validate='all', validatecommand=(valFloat, '%P'))
    gearingEntry.configure(state='disabled')
    gearingEntry.grid(row=6, column=1)

    Label(fbFrame, text='Encoder PPR:', anchor='e').grid(
        row=7, column=0, sticky='ew')
    pprEntry = Entry(fbFrame, textvariable=STATE.encoder_ppr, width=10,
                     validate='all', validatecommand=(valInt, '%P'))
    pprEntry.configure(state='disabled')
    pprEntry.grid(row=7, column=1)

    Label(fbFrame, text='Has Slave:', anchor='e').grid(
        row=8, column=0, sticky='ew')
    hasSlave = Checkbutton(fbFrame, variable=STATE.has_slave)
    hasSlave.grid(row=8, column=1)
    hasSlave.configure(state='disabled')
    STATE.has_slave.trace_add('write', enableOffboard)

    Label(fbFrame, text='Slave Update Period (s):',
          anchor='e').grid(row=9, column=0, sticky='ew')
    slavePeriodEntry = Entry(fbFrame, textvariable=STATE.slave_period, width=10,
                             validate='all', validatecommand=(valFloat, '%P'))
    slavePeriodEntry.grid(row=9, column=1)
    slavePeriodEntry.configure(state='disabled')

    Label(fbFrame, text='Max Acceptable Position Error (units):', anchor='e').grid(
        row=1, column=2, columnspan=2, sticky='ew')
    qPEntry = Entry(fbFrame, textvariable=STATE.qp, width=10,
                    validate='all', validatecommand=(valFloat, '%P'))
    qPEntry.grid(row=1, column=4)

    Label(fbFrame, text='Max Acceptable Velocity Error (units/s):', anchor='e').grid(
        row=2, column=2, columnspan=2, sticky='ew')
    qVEntry = Entry(fbFrame, textvariable=STATE.qv, width=10,
                    validate='all', validatecommand=(valFloat, '%P'))
    qVEntry.grid(row=2, column=4)

    Label(fbFrame, text='Max Acceptable Control Effort (V):', anchor='e').grid(
        row=3, column=2, columnspan=2, sticky='ew')
    effortEntry = Entry(fbFrame, textvariable=STATE.max_effort, width=10,
                        validate='all', validatecommand=(valFloat, '%P'))
    effortEntry.grid(row=3, column=4)

    Label(fbFrame, text='kV:', anchor='e').grid(row=5, column=2, sticky='ew')
    kVFBEntry = Entry(fbFrame, textvariable=STATE.kv, width=10,
                      validate='all', validatecommand=(valFloat, '%P'))
    kVFBEntry.grid(row=5, column=3)
    Label(fbFrame, text='kA:', anchor='e').grid(row=6, column=2, sticky='ew')
    kAFBEntry = Entry(fbFrame, textvariable=STATE.ka, width=10,
                      validate='all', validatecommand=(valFloat, '%P'))
    kAFBEntry.grid(row=6, column=3)

    calcGainsButton = Button(fbFrame, text='Calculate Optimal Controller Gains',
                             command=calcGains, state='disabled')
    calcGainsButton.grid(row=7, column=2, columnspan=3)

    Label(fbFrame, text='kP:', anchor='e').grid(row=8, column=2, sticky='ew')
    kPEntry = Entry(fbFrame, textvariable=STATE.kp, width=10,
                    state='readonly').grid(row=8, column=3)

    Label(fbFrame, text='kD:', anchor='e').grid(row=9, column=2, sticky='ew')
    kDEntry = Entry(fbFrame, textvariable=STATE.kd, width=10,
                    state='readonly').grid(row=9, column=3)


#
# You probably don't have to change anything else
#

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
PREPARED_COS_COL = 5

PREPARED_MAX_COL = PREPARED_ACC_COL

JSON_DATA_KEYS = ["slow-forward", "slow-backward",
                  "fast-forward", "fast-backward"]

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


def trim_quasi_testdata(data):
    adata = np.abs(data)
    truth = np.all(
        [
            adata[ENCODER_V_COL] > STATE.motion_threshold.get(),
            adata[VOLTS_COL] > 0
        ],
        axis=0,
    )
    temp = data.transpose()[truth].transpose()
    if temp[PREPARED_TM_COL].size == 0:
        tkinter.messagebox.showinfo("Error!", "No data in quasistatic test is above motion threshold. "
                                    + "Try running with a smaller motion threshold "
                                    + "and make sure your encoder is reporting correctly!")
        return None
    else:
        return temp


def trim_step_testdata(data):
    # removes anything before the max acceleration
    max_accel_idx = np.argmax(np.abs(data[PREPARED_ACC_COL]))
    return data[:, max_accel_idx + 1:]


def compute_accel(data, window):
    """
        Returned data columns correspond to PREPARED_*
    """

    # deal with incomplete data
    if len(data[TIME_COL]) < window * 2:
        tkinter.messagebox.showinfo("Error!", "Not enough data points to compute acceleration. "
                                    + "Try running with a smaller window setting or a smaller threshold.")
        return None

    # Compute left/right acceleration
    acc = smoothDerivative(data[TIME_COL], data[ENCODER_V_COL], window)

    # Compute cosine of angle
    cos = np.array([math.cos(math.radians(x)) for x in data[ENCODER_P_COL]])

    dat = np.vstack(
        (
            data[TIME_COL],
            data[VOLTS_COL],
            data[ENCODER_P_COL],
            data[ENCODER_V_COL],
            acc,
            cos
        )
    )

    return dat


def prepare_data(data, window):
    """
        Firstly, data should be "trimmed" to exclude any data points at which the
        robot was not being commanded to do anything.

        Secondly, robot acceleration should be calculated from robot velocity and time.
        We have found it effective to do this by taking the slope of the secant line
        of velocity over a 60ms (3 standard loop iterations) window.

        Thirdly, data from the quasi-static test should be trimmed to exclude the
        initial period in which the robot is not moving due to static friction
        Fourthly, data from the step-voltage acceleration tests must be trimmed to
        remove the initial "ramp-up" period that exists due to motor inductance; this
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

    # Ensure voltage points in same direction as velocity
    for x in JSON_DATA_KEYS:
        data[x][VOLTS_COL] = np.copysign(
            data[x][VOLTS_COL], data[x][ENCODER_V_COL])

    # trim quasi data before computing acceleration
    sf_trim = trim_quasi_testdata(data["slow-forward"])
    sb_trim = trim_quasi_testdata(data["slow-backward"])

    if sf_trim is None or sb_trim is None:
        return None, None, None, None

    sf = compute_accel(sf_trim, window)
    sb = compute_accel(sb_trim, window)

    if sf is None or sb is None:
        return None, None, None, None

    # trim step data after computing acceleration
    ff = compute_accel(data["fast-forward"], window)
    fb = compute_accel(data["fast-backward"], window)

    if ff is None or fb is None:
        return None, None, None, None

    ff = trim_step_testdata(ff)
    fb = trim_step_testdata(fb)

    return sf, sb, ff, fb

# Now that we have useful data, perform linear regression on it


def ols(x1, x2, x3, y):
    """multivariate linear regression using ordinary least squares"""
    x = np.array((np.sign(x1), x1, x2, x3)).T
    model = sm.OLS(y, x)
    return model.fit()


def _plotTimeDomain(direction, qu, step):
    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    # Time-domain plots.
    # These should show if anything went horribly wrong during the tests.
    # Useful for diagnosing the data trim; quasistatic test should look purely linear with no leading "tail"

    plt.figure(direction + " Time-Domain Plots")

    # quasistatic vel and accel vs time
    ax1 = plt.subplot(221)
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Velocity")
    ax1.set_title("Quasistatic velocity vs time")
    plt.scatter(qu[PREPARED_TM_COL], qu[PREPARED_VEL_COL],
                marker=".", c="#000000")

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
    plt.scatter(qu[PREPARED_TM_COL], qu[PREPARED_ACC_COL],
                marker=".", c="#000000")

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


def _plotVoltageDomain(direction, qu, step):

    # Voltage-domain plots
    # These should show linearity of velocity/acceleration data with voltage
    # X-axis is not raw voltage, but rather "portion of voltage corresponding to vel/acc"
    # Both plots should be straight lines through the origin
    # Fit lines will be straight lines through the origin by construction; data should match fit

    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    ks = STATE.ks.get()
    kv = STATE.kv.get()
    ka = STATE.ka.get()
    kcos = STATE.kcos.get()
    r_square = STATE.r_square.get()

    plt.figure(direction + " Voltage-Domain Plots")

    # quasistatic vel vs. vel-causing voltage
    ax = plt.subplot(211)
    ax.set_xlabel("Velocity-Portion Voltage")
    ax.set_ylabel("Velocity")
    ax.set_title("Quasistatic velocity vs velocity-portion voltage")
    plt.scatter(
        qu[PREPARED_V_COL] - ks * np.sign(qu[PREPARED_VEL_COL]) - ka *
        qu[PREPARED_ACC_COL] - kcos * qu[PREPARED_COS_COL],
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
        step[PREPARED_V_COL] - ks * np.sign(step[PREPARED_VEL_COL]) - kv *
        step[PREPARED_VEL_COL] - kcos * step[PREPARED_COS_COL],
        step[PREPARED_ACC_COL],
        marker=".",
        c="#000000",
    )

    # show fit line from multiple regression
    y = np.linspace(np.min(step[PREPARED_ACC_COL]),
                    np.max(step[PREPARED_ACC_COL]))
    plt.plot(ka * y, y)

    # Fix overlapping axis labels
    plt.tight_layout(pad=0.5)

    plt.figure(direction + " Voltage-Domain Cosine Plot")

    # quasistatic position vs. gravity (cosine-term) voltage
    ax = plt.subplot(111)
    ax.set_xlabel("Gravity (cosine)-Portion Voltage")
    ax.set_ylabel("Angle")
    ax.set_title("Quasistatic angle vs gravity-portion voltage")
    plt.scatter(
        qu[PREPARED_V_COL] - ks * np.sign(qu[PREPARED_VEL_COL]) - kv *
        qu[PREPARED_VEL_COL] - ka * qu[PREPARED_ACC_COL],
        qu[PREPARED_POS_COL],
        marker=".",
        c="#000000",
    )

    # show fit line from multiple regression
    y = np.linspace(np.min(qu[PREPARED_POS_COL]), np.max(qu[PREPARED_POS_COL]))
    plt.plot(kcos * np.cos(np.radians(y)), y)

    # Fix overlapping axis labels
    plt.tight_layout(pad=0.5)

    plt.show()


def _plot3D(direction, qu, step):

    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    ks = STATE.ks.get()
    kv = STATE.kv.get()
    ka = STATE.ka.get()
    kcos = STATE.kcos.get()
    r_square = STATE.r_square.get()

    # Interactive 3d plot of voltage over entire vel-accel plane
    # Really cool, not really any more diagnostically-useful than prior plots but worth seeing
    plt.figure(direction + " 3D Vel-Accel Plane Plot")

    ax = plt.subplot(111, projection="3d")

    # 3D scatterplot
    ax.set_xlabel("Velocity")
    ax.set_ylabel("Acceleration")
    ax.set_zlabel("Voltage")
    ax.set_title("Cosine-adjusted Voltage vs velocity and acceleration")
    ax.scatter(vel, accel, volts - kcos * cos)

    # Show best fit plane
    vv, aa = np.meshgrid(
        np.linspace(np.min(vel), np.max(vel)),
        np.linspace(np.min(accel), np.max(accel)),
    )
    ax.plot_surface(vv, aa, ks * np.sign(vv) + kv * vv +
                    ka * aa, alpha=0.2, color=[0, 1, 1])

    plt.show()


def calcFit(qu, step):
    vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
    accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
    cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
    volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
    time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

    fit = ols(vel, accel, cos, volts)
    ks, kv, ka, kcos = fit.params
    rsquare = fit.rsquared

    return ks, kv, ka, kcos, rsquare


def _calcGains(kv, ka, qp, qv, effort, period):

    A = np.array([[0, 1], [0, -kv / ka]])
    B = np.array([[0], [1 / ka]])
    C = np.array([[1, 0]])
    D = np.array([[0]])
    sys = cnt.ss(A, B, C, D)
    dsys = sys.sample(period)

    # Assign Q and R matrices according to Bryson's rule [1]. The elements
    # of q and r are tunable by the user.
    #
    # [1] "Bryson's rule" in
    #     https://file.tavsys.net/control/state-space-guide.pdf
    q = [qp, qv]  # units and units/s acceptable errors
    r = [effort]  # V acceptable actuation effort
    Q = np.diag(1.0 / np.square(q))
    R = np.diag(1.0 / np.square(r))
    K = frccnt.lqr(dsys, Q, R)

    kp = K[0, 0]
    kd = K[0, 1]

    return kp, kd


def main():

    global mainGUI, STATE
    mainGUI = tkinter.Tk()
    STATE = ProgramState()

    mainGUI.deiconify()
    mainGUI.title("RobotPy Arm Characterization Tool")

    configure_gui()

    mainGUI.mainloop()


if __name__ == "__main__":
    main()
    
