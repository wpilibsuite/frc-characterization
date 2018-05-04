#!/usr/bin/env python3
#
# This is a very simple robot program that can be used to send telemetry to
# the data_logger script to characterize your drivetrain. If you wish to use
# your actual robot code, you only need to implement the simple logic in the
# autonomousPeriodic function and change the NetworkTables update rate
#

import math

import wpilib
from wpilib.drive import DifferentialDrive

from networktables import NetworkTables
from networktables.util import ntproperty


class MyRobot(wpilib.TimedRobot):
    '''Main robot class'''
    
    # NetworkTables API for controlling this
    
    #: Speed to set the motors to
    autospeed = ntproperty('/robot/autospeed', defaultValue=0, writeDefault=True)
    
    #: Test data that the robot sends back
    telemetry = ntproperty('/robot/telemetry', defaultValue=(0,)*9, writeDefault=False)
    
    prior_autospeed = 0
    
    WHEEL_DIAMETER = 0.5
    ENCODER_PULSE_PER_REV = 360
    
    def robotInit(self):
        '''Robot-wide initialization code should go here'''
        
        self.lstick = wpilib.Joystick(0)
        
        self.lr_motor = wpilib.Spark(1)
        self.lr_motor.setInverted(False)
        
        self.rr_motor = wpilib.Spark(2)
        self.rr_motor.setInverted(False)
        
        self.lf_motor = wpilib.Spark(3)
        self.lf_motor.setInverted(False)
        
        self.rf_motor = wpilib.Spark(4)
        self.rf_motor.setInverted(False)
        
        self.l_encoder = wpilib.Encoder(0, 1)
        self.l_encoder.setDistancePerPulse((1/self.ENCODER_PULSE_PER_REV) * self.WHEEL_DIAMETER * math.pi)
        self.l_encoder_getpos = self.l_encoder.getDistance
        self.l_encoder_getrate = self.l_encoder.getRate
        
        self.r_encoder = wpilib.Encoder(2, 3)
        self.r_encoder.setDistancePerPulse((1/self.ENCODER_PULSE_PER_REV) * self.WHEEL_DIAMETER * math.pi)
        self.r_encoder_getpos = self.r_encoder.getDistance
        self.r_encoder_getrate = self.r_encoder.getRate
        
        l = wpilib.SpeedControllerGroup(self.rf_motor, self.rr_motor)
        r = wpilib.SpeedControllerGroup(self.lf_motor, self.lr_motor)
        
        self.drive = DifferentialDrive(l, r)
        self.drive.setSafetyEnabled(False)
        self.drive.setDeadband(0)
        
        # Set the update rate instead of using flush because of a NetworkTables bug
        # that affects ntcore and pynetworktables
        NetworkTables.setUpdateRate(0.010)
        
    def disabledInit(self):
        self.logger.info("Robot disabled")
        self.drive.tankDrive(0, 0)
    
    def disabledPeriodic(self):
        pass

    def robotPeriodic(self):
        # feedback for users, but not used by the control program
        wpilib.SmartDashboard.putNumber('l_encoder_pos', self.l_encoder_getpos())
        wpilib.SmartDashboard.putNumber('l_encoder_rate', self.l_encoder_getrate())
    
    def teleopInit(self):
        self.logger.info("Robot in operator control mode")
    
    def teleopPeriodic(self):
        self.drive.arcadeDrive(-self.lstick.getY(), self.lstick.getX())
    
    def autonomousInit(self):
        self.logger.info("Robot in autonomous mode")
    
    def autonomousPeriodic(self):
        '''
            If you wish to just use your own robot program to use with the data
            logging program, you only need to copy/paste the logic below into
            your code and ensure it gets called periodically in autonomous mode
            
            Additionally, you need to set NetworkTables update rate to 10ms using
            the setUpdateRate call.
            
            Note that reading/writing self.autospeed and self.telemetry are
            NetworkTables operations (using pynetworktables's ntproperty), so
            if you don't read/write NetworkTables in your implementation it won't
            actually work.
        '''
        
        # Retrieve values to send back
        now = wpilib.Timer.getFPGATimestamp()
        
        l_encoder_value = self.l_encoder_getpos()
        l_encoder_rate = self.l_encoder_getrate()
        
        r_encoder_value = self.r_encoder_getpos()
        r_encoder_rate = self.r_encoder_getrate()
        
        battery = self.ds.getBatteryVoltage()
        motor_volts = battery * abs(self.prior_autospeed)
        
        # Retrieve the commanded speed from NetworkTables
        autospeed = self.autospeed
        self.prior_autospeed = autospeed
        
        # command motors to do things
        self.drive.tankDrive(autospeed, autospeed, False)
        
        # send telemetry data array back to NT
        self.telemetry = (now,
                          battery, autospeed,
                          motor_volts,
                          motor_volts,
                          l_encoder_value,
                          r_encoder_value,
                          l_encoder_rate,
                          r_encoder_rate)


if __name__ == '__main__':
    wpilib.run(MyRobot)
