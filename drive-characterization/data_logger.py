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

from data_analyzer import analyze_data, AUTOSPEED_COL, L_ENCODER_P_COL, R_ENCODER_P_COL

import logging

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


class DataLogger:

    # Change this key to whatever NT key you want to log
    log_key = "/robot/telemetry"

    matchNumber = ntproperty("/FMSInfo/MatchNumber", 0, writeDefault=False)
    eventName = ntproperty("/FMSInfo/EventName", "unknown", writeDefault=False)

    autospeed = ntproperty("/robot/autospeed", 0, writeDefault=True)

    def __init__(self):
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

                # Don't block the NT thread -- trite the data to the queue so
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

        # Initialize networktables
        team = ""
        while team == "":
            team = input("Enter team number or 'sim': ")

        if team == "sim":
            NetworkTables.initialize(server="localhost")
        else:
            NetworkTables.startClientTeam(int(team))

        # Use listeners to receive the data
        NetworkTables.addConnectionListener(
            self.connectionListener, immediateNotify=True
        )
        NetworkTables.addEntryListener(self.valueChanged)

        # Wait for a connection notification, then continue on the path
        print("Waiting for NT connection..")
        while True:
            if self.queue.get() == "connected":
                break

        print("Connected!")
        print()

        autonomous = [
            # name, initial speed, ramp
            ("slow-forward", 0, 0.001),
            ("slow-backward", 0, -0.001),
            ("fast-forward", abs(ROBOT_FAST_SPEED), 0),
            ("fast-backward", -abs(ROBOT_FAST_SPEED), 0),
        ]

        stored_data = {}

        #
        # Wait for the user to cycle through the 4 autonomus modes
        #

        for i, (name, initial_speed, ramp) in enumerate(autonomous):

            # Initialize the robot commanded speed to 0
            self.autospeed = 0
            self.discard_data = True

            print()
            print("Autonomous %d/%d: %s" % (i + 1, len(autonomous), name))
            print()
            print("Please enable the robot in autonomous mode.")
            print()
            print(
                "WARNING: It will not automatically stop moving, so disable the robot"
            )
            print("before it hits something!")
            print("")

            # Wait for robot to signal that it entered autonomous mode
            with self.lock:
                self.lock.wait_for(lambda: self.mode == "auto")

            data = self.wait_for_stationary()
            if data is not None:
                if data in ("connected", "disconnected"):
                    print(
                        "ERROR: NT disconnected, results won't be reliable. Giving up."
                    )
                    return
                else:
                    print("Robot exited autonomous mode before data could be sent?")
                    break

            # Ramp the voltage at the specified rate
            data = self.ramp_voltage_in_auto(initial_speed, ramp)
            if data in ("connected", "disconnected"):
                print("ERROR: NT disconnected, results won't be reliable. Giving up.")
                return

            # output sanity check
            if len(data) < 3:
                print(
                    "WARNING: There wasn't a lot of data received during that last run"
                )
            else:
                left_distance = data[-1][L_ENCODER_P_COL] - data[0][L_ENCODER_P_COL]
                right_distance = data[-1][R_ENCODER_P_COL] - data[0][R_ENCODER_P_COL]

                print()
                print("The robot reported traveling the following distance:")
                print()
                print("Left:  %.3f ft" % left_distance)
                print("Right: %.3f ft" % right_distance)
                print()
                print(
                    "If that doesn't seem quite right... you should change the encoder calibration"
                )
                print("in the robot program or fix your encoders!")

            stored_data[name] = data

        # In case the user decides to re-enable autonomous again..
        self.autospeed = 0

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


if __name__ == "__main__":

    log_datefmt = "%H:%M:%S"
    log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"

    logging.basicConfig(level=logging.INFO, datefmt=log_datefmt, format=log_format)

    dl = DataLogger()
    dl.run()
