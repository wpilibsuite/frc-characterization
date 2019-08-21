/*----------------------------------------------------------------------------*/
/* Copyright (c) 2018 FIRST. All Rights Reserved.                             */
/* Open Source Software - may be modified and shared by FRC teams. The code   */
/* must be accompanied by the FIRST BSD license file in the root directory of */
/* the project.                                                               */
/*----------------------------------------------------------------------------*/

#include "Robot.h"
#include <frc/smartdashboard/SmartDashboard.h>
#include <frc/RobotController.h>
#include <iostream>

void Robot::RobotInit() {
    m_leftFrontMotor.SetInverted(false);
    m_leftFrontMotor.SetSensorPhase(false);
    m_leftFrontMotor.SetNeutralMode(NeutralMode::Brake);

    m_rightFrontMotor.SetInverted(false);
    m_rightFrontMotor.SetSensorPhase(true);
    m_rightFrontMotor.SetNeutralMode(NeutralMode::Brake);

    m_leftRearMotor.SetInverted(false);
    m_leftRearMotor.SetSensorPhase(false);
    m_leftRearMotor.Follow(m_leftFrontMotor);
    m_leftRearMotor.SetNeutralMode(NeutralMode::Brake);

    m_rightRearMotor.SetInverted(false);
    m_rightRearMotor.SetSensorPhase(true);
    m_rightRearMotor.Follow(m_rightFrontMotor);
    m_rightRearMotor.SetNeutralMode(NeutralMode::Brake);

    m_drive.SetDeadband(0);

    m_leftFrontMotor.ConfigSelectedFeedbackSensor(FeedbackDevice::QuadEncoder,
                                                  kPIDIdx, 10);
    m_rightFrontMotor.ConfigSelectedFeedbackSensor(FeedbackDevice::QuadEncoder,
                                                   kPIDIdx, 10);

    m_leftFrontMotor.SetSelectedSensorPosition(0);
    m_rightFrontMotor.SetSelectedSensorPosition(0);

    nt::NetworkTableInstance::GetDefault().SetUpdateRate(0.010);
}

void Robot::RobotPeriodic() {
    frc::SmartDashboard::PutNumber("l_encoder_pos", m_leftEncoderPosition());
    frc::SmartDashboard::PutNumber("l_encoder_rate", m_leftEncoderRate());
    frc::SmartDashboard::PutNumber("r_encoder_pos", m_rightEncoderPosition());
    frc::SmartDashboard::PutNumber("r_encoder_rate", m_rightEncoderRate());
    frc::SmartDashboard::PutNumber("gyro_angle", m_gyroAngleRadians());
}

void Robot::DisabledInit() {
    std::cout << "Robot Disabled";
    m_drive.TankDrive(0, 0);
}

void Robot::AutonomousInit() { std::cout << "Robot in autonomous mode"; }
void Robot::AutonomousPeriodic() {
    double autoSpeed = m_autoSpeedEntry.GetDouble(0);
    priorAutoSpeed = autoSpeed;

    double numberArray[]{frc::Timer::GetFPGATimestamp(),
                         frc::RobotController::GetInputVoltage(),
                         autoSpeed,
                         m_leftFrontMotor.GetMotorOutputVoltage(),
                         m_rightFrontMotor.GetMotorOutputVoltage(),
                         m_leftEncoderPosition(),
                         m_rightEncoderPosition(),
                         m_leftEncoderRate(),
                         m_rightEncoderRate(),
                         m_gyroAngleRadians()};

    m_drive.TankDrive(autoSpeed, autoSpeed, false);

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
