#!/usr/bin/env python3
#
# This analyzes the data collected by the data_logger.py script. It is ran
# automatically after the data_logger.py script is ran, but you can also
# invoke it separately and give it JSON data to analyze.
#
# The analysis and data cleanup is carried out in accordance with the
# specification at https://www.chiefdelphi.com/forums/showthread.php?t=161539
#

import json
import sys

import numpy as np
import matplotlib.pyplot as plt

#
# These parameters are used to indicate which column of data each parameter
# can be found at
#

TIME_COL = 0
BATTERY_COL = 1
AUTOSPEED_COL = 2
L_VOLTS_COL = 3
R_VOLTS_COL = 4
L_ENCODER_P_COL = 5
R_ENCODER_P_COL = 6
L_ENCODER_V_COL = 7
R_ENCODER_V_COL = 8

WINDOW = 2
MOTION_THRESHOLD = 0.1


# From 449's R script
def smoothDerivative(tm, value, n, off):
    '''
        :param tm: time column
        :param value: Value to take the derivative of
        :param off: Offset of time column start position
    '''
    dlen = len(value)
    dt = tm[n+1+off:dlen+off] - tm[1+off:(dlen-n)+off]
    x = (value[(n+1):dlen] - value[1:(dlen-n)]) / dt
    return x

# trim functions: expect array of tm, volts, velocity, acceleration
TRIM_TM_COL = 0
TRIM_V_COL = 1
TRIM_POS_COL = 2
TRIM_VEL_COL = 3
TRIM_ACC_COL = 4

def trim_quasi_testdata(data):
    # removes initial minimal velocity points
    for i,v  in enumerate(data[TRIM_VEL_COL]):
        if abs(v) > 0.1:
            break
    return data[:,i:]
    
def trim_step_testdata(data):
    # removes anything before the max acceleration
    max_accel_idx = np.argmax(np.abs(data[TRIM_ACC_COL]))
    return data[:,max_accel_idx:]

def prepare_data(data, trimfn):
    
    # Transform the data into a numpy array to make it easier to use
    data = np.array(data).transpose()
    
    # We only have position, so compute velocity/acceleration for each side
    #l_vel = smoothDerivative(data[TIME_COL], data[L_ENCODER_V_COL], WINDOW, 0)
    l_acc = smoothDerivative(data[TIME_COL], data[L_ENCODER_V_COL], WINDOW, 0)
    
    #r_vel = smoothDerivative(data[TIME_COL], data[R_ENCODER_COL], WINDOW, 0)
    r_acc = smoothDerivative(data[TIME_COL], data[R_ENCODER_V_COL], WINDOW, 0)
    
    # trim data to ensure it's all the same length to ease analysis
    data = data[:,1:-WINDOW]
    
    l = np.vstack((data[TIME_COL], data[L_VOLTS_COL], data[L_ENCODER_P_COL], data[L_ENCODER_V_COL], l_acc))
    r = np.vstack((data[TIME_COL], data[R_VOLTS_COL], data[R_ENCODER_P_COL], data[R_ENCODER_V_COL], r_acc))
    
    l = trimfn(l)
    r = trimfn(r)

    return l, r


def analyze_data(data):
    '''
        Firstly, data should be "trimmed" to exclude any data points at which the
        robot was not being commanded to do anything. [we don't have to do this]
        
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
    '''
    
    sf_l, sf_r = prepare_data(data['slow-forward'], trim_quasi_testdata)
    sb_l, sb_r = prepare_data(data['slow-backward'], trim_quasi_testdata)

    ff_l, ff_r = prepare_data(data['fast-forward'], trim_step_testdata)
    fb_l, fb_r = prepare_data(data['fast-backward'], trim_step_testdata)
    
    # Now that we have useful data, perform linear regression on it
    # -> TODO: figure out how to combine the data...
    
    def _print(n, pfx, qu, step):
        kv, vi = np.polyfit(qu[TRIM_VEL_COL], qu[TRIM_V_COL], 1)
        ka, kai = np.polyfit(step[TRIM_ACC_COL], step[TRIM_V_COL], 1)
        txt = "%s:  kv=%.3f ka=%.3f vintercept=%.3f" % (pfx, kv, ka, vi)
        print(txt)
        
        plt.figure(txt)
        
        plt.subplot(211)
        plt.plot(qu[TRIM_V_COL], qu[TRIM_VEL_COL])
        
        # show the fit
        y = np.linspace(np.min(qu[TRIM_VEL_COL]), np.max(qu[TRIM_VEL_COL]))
        plt.plot(kv*y + vi, y)
        
        plt.subplot(212)
        plt.plot(step[TRIM_V_COL], step[TRIM_ACC_COL])
        
        y = np.linspace(np.min(step[TRIM_ACC_COL]), np.max(step[TRIM_ACC_COL]))
        plt.plot(ka*y + kai, y)
    
    # kv and vintercept is computed from the first two tests, ka from the latter
    _print(1, 'Left forward  ', sf_l, ff_l)
    _print(2, 'Left backward ', sb_l, fb_l)
    
    _print(3, 'Right forward ', sf_r, ff_r)
    _print(4, 'Right backward', sb_r, fb_r)
    
    plt.show()
    

def main():
    with open(sys.argv[1], 'r') as fp:
        stored_data = json.load(fp)

    analyze_data(stored_data)

if __name__ == '__main__':
    main()
