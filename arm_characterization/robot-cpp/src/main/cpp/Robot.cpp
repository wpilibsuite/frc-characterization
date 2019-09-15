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
    m_armMotor.SetInverted(false);

    constexpr double kEncoderConstant =
        (1 / kEncoderPulsePerRev) / kGearing * 360.;

    m_encoder.SetDistancePerPulse(kEncoderConstant);

    nt::NetworkTableInstance::GetDefault().SetUpdateRate(0.010);
}

void Robot::RobotPeriodic() {
    frc::SmartDashboard::PutNumber("encoder_pos", m_encoderPosition());
    frc::SmartDashboard::PutNumber("encoder_rate", m_encoderRate());
}

void Robot::DisabledInit() {
    std::cout << "Robot Disabled";
    m_armMotor.Set(0.0);
}

void Robot::AutonomousInit() { std::cout << "Robot in autonomous mode"; }
void Robot::AutonomousPeriodic() {
    double battery = frc::RobotController::GetInputVoltage();
    double motorVolts = battery * std::abs(priorAutoSpeed);

    double autoSpeed = m_autoSpeedEntry.GetDouble(0);
    priorAutoSpeed = autoSpeed;

    double numberArray[]{frc::Timer::GetFPGATimestamp(),
                         battery,
                         autoSpeed,
                         motorVolts,
                         m_encoderPosition(),
                         m_encoderRate()};

    m_armMotor.Set(autoSpeed);

    m_telemetryEntry.SetDoubleArray(numberArray);
}

void Robot::TeleopInit() { std::cout << "Robot in operator control mode"; }
void Robot::TeleopPeriodic() { m_armMotor.Set(-m_joystick.GetY()); }

void Robot::TestInit() {}
void Robot::TestPeriodic() {}

#ifndef RUNNING_FRC_TESTS
int main() { return frc::StartRobot<Robot>(); }
#endif
