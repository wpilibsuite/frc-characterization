/*----------------------------------------------------------------------------*/
/* Copyright (c) 2018 FIRST. All Rights Reserved.                             */
/* Open Source Software - may be modified and shared by FRC teams. The code   */
/* must be accompanied by the FIRST BSD license file in the root directory of */
/* the project.                                                               */
/*----------------------------------------------------------------------------*/

#include "Robot.h"

#include <frc/smartdashboard/SmartDashboard.h>
#include <frc/Timer.h>
#include <frc/RobotController.h>
#include <iostream>

void Robot::RobotInit() {
    m_leftFrontMotor.SetInverted(false);
    m_rightFrontMotor.SetInverted(false);
    m_leftRearMotor.SetInverted(false);
    m_rightRearMotor.SetInverted(false);

    m_drive.SetDeadband(0);

    constexpr double kEncoderConstant =
        (1 / kEncoderPulsePerRev) * kWheelDiameter * 3.1415926535;

    m_leftEncoder.SetDistancePerPulse(kEncoderConstant);
    m_rightEncoder.SetDistancePerPulse(kEncoderConstant);

    nt::NetworkTableInstance::GetDefault().SetUpdateRate(0.010);
}

void Robot::RobotPeriodic() {
    frc::SmartDashboard::PutNumber("l_encoder_pos", m_leftEncoderPosition());
    frc::SmartDashboard::PutNumber("l_encoder_rate", m_leftEncoderRate());
    frc::SmartDashboard::PutNumber("r_encoder_pos", m_rightEncoderPosition());
    frc::SmartDashboard::PutNumber("r_encoder_rate", m_rightEncoderRate());
}

void Robot::DisabledInit() {
    std::cout << "Robot Disabled";
    m_drive.TankDrive(0, 0);
}

void Robot::AutonomousInit() { std::cout << "Robot in autonomous mode"; }
void Robot::AutonomousPeriodic() {

    static double numberArray[9];

    double now = frc::Timer::GetFPGATimestamp();

    double leftPosition = m_leftEncoderPosition();
    double leftRate = m_leftEncoderRate();

    double rightPosition = m_rightEncoderPosition();
    double rightRate = m_rightEncoderRate();

    double battery = frc::RobotController::GetInputVoltage();
    double motorVolts = battery * std::abs(priorAutoSpeed);

    double leftMotorVolts = motorVolts;
    double rightMotorVolts = motorVolts;

    double autoSpeed = m_autoSpeedEntry.GetDouble(0);
    priorAutoSpeed = autoSpeed;

    m_drive.TankDrive(autoSpeed, autoSpeed, false);

    numberArray[0] = now;
    numberArray[1] = battery;
    numberArray[2] = autoSpeed;
    numberArray[3] = leftMotorVolts;
    numberArray[4] = rightMotorVolts;
    numberArray[5] = leftPosition;
    numberArray[6] = rightPosition;
    numberArray[7] = leftRate;
    numberArray[8] = rightRate;

    m_telemetryEntry.SetDoubleArray(numberArray);
}

void Robot::TeleopInit() { std::cout << "Robot in operator control mode"; }
void Robot::TeleopPeriodic() {
    m_drive.ArcadeDrive(-m_joystick.GetY(), m_joystick.GetX());
}

void Robot::TestInit() {}
void Robot::TestPeriodic() {}

#ifndef RUNNING_FRC_TESTS
int main() { return frc::StartRobot<Robot>(); }
#endif
