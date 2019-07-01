#!/usr/bin/env python3
#
# This is a very simple robot program that can be used to send telemetry to
# the data_logger script to characterize your drivetrain. If you wish to use
# your actual robot code, you only need to implement the simple logic in the
# autonomousPeriodic function and change the NetworkTables update rate
#
# See http://robotpy.readthedocs.io/en/stable/install/robot.html for RobotPy
# installation instructions
#

import math

import wpilib
from wpilib.drive import DifferentialDrive

from networktables import NetworkTables
from networktables.util import ntproperty


class MyRobot(wpilib.TimedRobot):
    """Main robot class"""

    # NetworkTables API for controlling this

    #: Speed to set the motors to
    autospeed = ntproperty("/robot/autospeed", defaultValue=0, writeDefault=True)

    #: Test data that the robot sends back
    telemetry = ntproperty(
        "/robot/telemetry", defaultValue=(0,) * 6, writeDefault=False
    )

    prior_autospeed = 0

    #: The total gear reduction between the encoder and the arm
    GEARING = 1
    #: The offset of encoder zero from horizontal, in degrees.
	#: It is CRUCIAL that this be set correctly, or the characterization will not work!
    OFFSET = 0
    ENCODER_PULSE_PER_REV = 360

    def robotInit(self):
        """Robot-wide initialization code should go here"""

        self.lstick = wpilib.Joystick(0)

        self.arm_motor = wpilib.Spark(1)
        self.arm_motor.setInverted(False)

        #
        # Configure encoder related functions -- getpos and getrate should return
        # degrees and degrees/s
        #

        encoder_constant = (
            (1 / self.ENCODER_PULSE_PER_REV) / self.GEARING * 360
        )

        encoder = wpilib.Encoder(0, 1)
        encoder.setDistancePerPulse(encoder_constant)
        self.encoder_getpos = (lambda: encoder.getDistance() + self.OFFSET)
        self.encoder_getrate = encoder.getRate

        # Set the update rate instead of using flush because of a NetworkTables bug
        # that affects ntcore and pynetworktables
        # -> probably don't want to do this on a robot in competition
        NetworkTables.setUpdateRate(0.010)

    def disabledInit(self):
        self.logger.info("Robot disabled")
        self.arm_motor.set(0)

    def disabledPeriodic(self):
        pass

    def robotPeriodic(self):
        # feedback for users, but not used by the control program
        sd = wpilib.SmartDashboard
        sd.putNumber("encoder_pos", self.encoder_getpos())
        sd.putNumber("encoder_rate", self.encoder_getrate())

    def teleopInit(self):
        self.logger.info("Robot in operator control mode")

    def teleopPeriodic(self):
        self.arm_motor.set(-self.lstick.getY())

    def autonomousInit(self):
        self.logger.info("Robot in autonomous mode")

    def autonomousPeriodic(self):
        """
            If you wish to just use your own robot program to use with the data
            logging program, you only need to copy/paste the logic below into
            your code and ensure it gets called periodically in autonomous mode
            
            Additionally, you need to set NetworkTables update rate to 10ms using
            the setUpdateRate call.
            
            Note that reading/writing self.autospeed and self.telemetry are
            NetworkTables operations (using pynetworktables's ntproperty), so
            if you don't read/write NetworkTables in your implementation it won't
            actually work.
        """

        # Retrieve values to send back before telling the motors to do something
        now = wpilib.Timer.getFPGATimestamp()

        encoder_position = self.encoder_getpos()
        encoder_rate = self.encoder_getrate()

        battery = self.ds.getBatteryVoltage()
        motor_volts = battery * abs(self.prior_autospeed)

        # Retrieve the commanded speed from NetworkTables
        autospeed = self.autospeed
        self.prior_autospeed = autospeed

        # command motors to do things
        self.arm_motor.set(autospeed)

        # send telemetry data array back to NT
        self.telemetry = (
            now,
            battery,
            autospeed,
            motor_volts,
            encoder_position,
            encoder_rate
        )


if __name__ == "__main__":
    wpilib.run(MyRobot)
