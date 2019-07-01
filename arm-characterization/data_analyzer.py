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
from os.path import basename, exists, dirname, join, splitext

import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from mpl_toolkits.mplot3d import Axes3D

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

WINDOW = 8
MOTION_THRESHOLD = 20

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


def trim_quasi_testdata(data):
    adata = np.abs(data)
    truth = np.all(
        [
            adata[ENCODER_V_COL] > MOTION_THRESHOLD,
            adata[VOLTS_COL] > 0
        ],
        axis=0,
    )
    return data.transpose()[truth].transpose()


def trim_step_testdata(data):
    # removes anything before the max acceleration
    max_accel_idx = np.argmax(np.abs(data[PREPARED_ACC_COL]))
    return data[:, max_accel_idx + 1 :]


def prepare_data(data, window):
    """
        Returned data columns correspond to PREPARED_*
    """

    # deal with incomplete data
    if len(data[TIME_COL]) < window * 2:
        return (
            np.zeros(shape=(PREPARED_MAX_COL + 1, 4)),
            np.zeros(shape=(PREPARED_MAX_COL + 1, 4)),
        )

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


def analyze_data(data, window=WINDOW):
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

    # Transform the data into a numpy array to make it easier to use
    # -> transpose it so we can deal with it in columns
    for k in JSON_DATA_KEYS:
        data[k] = np.array(data[k]).transpose()

    # trim quasi data before computing acceleration
    sf_trim = trim_quasi_testdata(data["slow-forward"])
    sb_trim = trim_quasi_testdata(data["slow-backward"])
    sf = prepare_data(sf_trim, window)
    sb = prepare_data(sb_trim, window)

    # trim step data after computing acceleration
    ff = prepare_data(data["fast-forward"], window)
    fb = prepare_data(data["fast-backward"], window)

    ff = trim_step_testdata(ff)
    fb = trim_step_testdata(fb)

    # Now that we have useful data, perform linear regression on it
    def _ols(x1, x2, x3, y):
        """multivariate linear regression using ordinary least squares"""
        x = np.array((x1, x2, x3)).T
        x = sm.add_constant(x)
        model = sm.OLS(y, x)
        return model.fit()

    def _print(n, pfx, qu, step):
        vel = np.concatenate((qu[PREPARED_VEL_COL], step[PREPARED_VEL_COL]))
        accel = np.concatenate((qu[PREPARED_ACC_COL], step[PREPARED_ACC_COL]))
        cos = np.concatenate((qu[PREPARED_COS_COL], step[PREPARED_COS_COL]))
        volts = np.concatenate((qu[PREPARED_V_COL], step[PREPARED_V_COL]))
        time = np.concatenate((qu[PREPARED_TM_COL], step[PREPARED_TM_COL]))

        fit = _ols(vel, accel, cos, volts)
        vi, kv, ka, kcos = fit.params
        rsquare = fit.rsquared

        txt = "%s:  kv=% .4f ka=% .4f kcos=% .4f vintercept=% .4f r-squared=% .4f" % (
            pfx,
            kv,
            ka,
            kcos,
            vi,
            rsquare,
        )
        print(txt)

        # Time-domain plots.
        # These should show if anything went horribly wrong during the tests.
        # Useful for diagnosing the data trim; quasistatic test should look purely linear with no leading "tail"

        plt.figure(pfx + " Time-Domain Plots")

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

        # Voltage-domain plots
        # These should show linearity of velocity/acceleration data with voltage
        # X-axis is not raw voltage, but rather "portion of voltage corresponding to vel/acc"
        # Both plots should be straight lines through the origin
        # Fit lines will be straight lines through the origin by construction; data should match fit

        plt.figure(pfx + " Voltage-Domain Plots")

        # quasistatic vel vs. vel-causing voltage
        ax = plt.subplot(211)
        ax.set_xlabel("Velocity-Portion Voltage")
        ax.set_ylabel("Velocity")
        ax.set_title("Quasistatic velocity vs velocity-portion voltage")
        plt.scatter(
            qu[PREPARED_V_COL] - vi - ka * qu[PREPARED_ACC_COL] - kcos * qu[PREPARED_COS_COL],
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
            step[PREPARED_V_COL] - vi - kv * step[PREPARED_VEL_COL] - kcos * step[PREPARED_COS_COL],
            step[PREPARED_ACC_COL],
            marker=".",
            c="#000000",
        )

        # show fit line from multiple regression
        y = np.linspace(np.min(step[PREPARED_ACC_COL]), np.max(step[PREPARED_ACC_COL]))
        plt.plot(ka * y, y)

        # Fix overlapping axis labels
        plt.tight_layout(pad=0.5)

        # Interactive 3d plot of voltage over entire vel-accel plane
        # Really cool, not really any more diagnostically-useful than prior plots but worth seeing
        plt.figure(pfx + " 3D Vel-Accel Plane Plot")

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
        ax.plot_surface(vv, aa, vi + kv * vv + ka * aa, alpha=0.2, color=[0, 1, 1])

    # kv and vintercept is computed from the first two tests, ka from the latter
    _print(1, "Left forward  ", sf, ff)
    _print(2, "Left backward ", sb, fb)

    plt.show()


def split_to_csv(fname, stored_data):

    outdir = dirname(fname)
    fname = join(outdir, splitext(basename(fname))[0])

    header = [""] * (max(columns.values()) + 1)
    for k, v in columns.items():
        header[v] = k

    for d in JSON_DATA_KEYS:
        fn = "%s-%s.csv" % (fname, d)
        if exists(fn):
            print("Error:", fn, "already exists")
            return

    for d in JSON_DATA_KEYS:
        fn = "%s-%s.csv" % (fname, d)
        with open(fn, "w") as fp:
            c = csv.writer(fp)
            c.writerow(header)
            for r in stored_data[d].transpose():
                c.writerow(r)


def fixup_data(stored_data, scale):
    for d in JSON_DATA_KEYS:
        data = np.array(stored_data[d]).transpose()

        data[ENCODER_P_COL] *= scale
        data[ENCODER_V_COL] *= scale

        stored_data[d] = data.transpose()


def main():

    parser = argparse.ArgumentParser(description="Analyze your data")
    parser.add_argument("jsonfile", help="Input JSON file")
    parser.add_argument("--to-csv", action="store_true", default=False)
    parser.add_argument(
        "--scale",
        default=1,
        type=float,
        help="Multiply position/velocity values by this",
    )
    parser.add_argument(
        "--window",
        default=WINDOW,
        type=int,
        help="Window size for computing acceleration",
    )
    args = parser.parse_args()

    with open(args.jsonfile, "r") as fp:
        stored_data = json.load(fp)

    fixup_data(stored_data, args.scale)

    if args.to_csv:
        split_to_csv(args.jsonfile, stored_data)
    else:
        analyze_data(stored_data, window=args.window)


if __name__ == "__main__":
    main()
