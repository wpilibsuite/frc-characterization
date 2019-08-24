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
        "/robot/telemetry", defaultValue=(0,) * 9, writeDefault=False
    )

    prior_autospeed = 0

    WHEEL_DIAMETER = 0.5
    ENCODER_PULSE_PER_REV = 360

    def robotInit(self):
        """Robot-wide initialization code should go here"""

        self.lstick = wpilib.Joystick(0)

        left_front_motor = wpilib.Spark(1)
        left_front_motor.setInverted(False)

        right_front_motor = wpilib.Spark(2)
        right_front_motor.setInverted(False)

        left_rear_motor = wpilib.Spark(3)
        left_rear_motor.setInverted(False)

        right_rear_motor = wpilib.Spark(4)
        right_rear_motor.setInverted(False)

        #
        # Configure drivetrain movement
        #

        l = wpilib.SpeedControllerGroup(left_front_motor, left_rear_motor)
        r = wpilib.SpeedControllerGroup(right_front_motor, right_rear_motor)

        self.drive = DifferentialDrive(l, r)
        self.drive.setSafetyEnabled(False)
        self.drive.setDeadband(0)

        #
        # Configure encoder related functions -- getpos and getrate should return
        # ft and ft/s
        #

        encoder_constant = (
            (1 / self.ENCODER_PULSE_PER_REV) * self.WHEEL_DIAMETER * math.pi
        )

        l_encoder = wpilib.Encoder(0, 1)
        l_encoder.setDistancePerPulse(encoder_constant)
        self.l_encoder_getpos = l_encoder.getDistance
        self.l_encoder_getrate = l_encoder.getRate

        r_encoder = wpilib.Encoder(2, 3)
        r_encoder.setDistancePerPulse(encoder_constant)
        self.r_encoder_getpos = r_encoder.getDistance
        self.r_encoder_getrate = r_encoder.getRate

        #
        # Configure gyro
        #

        # You only need to uncomment the below lines if you want to characterize wheelbase radius
		# Otherwise you can leave this area as-is
        self.gyro_getangle = lambda: 0

        # Uncomment for the KOP gyro
        # Note that the angle from all implementors of the Gyro class must be negated because
		# getAngle returns a clockwise angle, and we require a counter-clockwise one
        # gyro = ADXRS450_Gyro()
        # self.gyro_getangle = lambda: -1 * gyro.getAngle()

        # Set the update rate instead of using flush because of a NetworkTables bug
        # that affects ntcore and pynetworktables
        # -> probably don't want to do this on a robot in competition
        NetworkTables.setUpdateRate(0.010)

    def disabledInit(self):
        self.logger.info("Robot disabled")
        self.drive.tankDrive(0, 0)

    def disabledPeriodic(self):
        pass

    def robotPeriodic(self):
        # feedback for users, but not used by the control program
        sd = wpilib.SmartDashboard
        sd.putNumber("l_encoder_pos", self.l_encoder_getpos())
        sd.putNumber("l_encoder_rate", self.l_encoder_getrate())
        sd.putNumber("r_encoder_pos", self.r_encoder_getpos())
        sd.putNumber("r_encoder_rate", self.r_encoder_getrate())
        sd.putNumber("gyro_angle", self.gyro_getangle())

    def teleopInit(self):
        self.logger.info("Robot in operator control mode")

    def teleopPeriodic(self):
        self.drive.arcadeDrive(-self.lstick.getY(), self.lstick.getX())

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

        l_encoder_position = self.l_encoder_getpos()
        l_encoder_rate = self.l_encoder_getrate()

        r_encoder_position = self.r_encoder_getpos()
        r_encoder_rate = self.r_encoder_getrate()

        battery = self.ds.getBatteryVoltage()
        motor_volts = battery * abs(self.prior_autospeed)

        l_motor_volts = motor_volts
        r_motor_volts = motor_volts

        gyro_angle = self.gyro_getangle()

        # Retrieve the commanded speed from NetworkTables
        autospeed = self.autospeed
        self.prior_autospeed = autospeed

        # command motors to do things
        self.drive.tankDrive(autospeed, autospeed, False)

        # send telemetry data array back to NT
        self.telemetry = (
            now,
            battery,
            autospeed,
            l_motor_volts,
            r_motor_volts,
            l_encoder_position,
            r_encoder_position,
            l_encoder_rate,
            r_encoder_rate,
            gyro_angle,
        )


if __name__ == "__main__":
    wpilib.run(MyRobot)
