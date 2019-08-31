/*----------------------------------------------------------------------------*/
/* Copyright (c) 2018 FIRST. All Rights Reserved.                             */
/* Open Source Software - may be modified and shared by FRC teams. The code   */
/* must be accompanied by the FIRST BSD license file in the root directory of */
/* the project.                                                               */
/*----------------------------------------------------------------------------*/

#pragma once

#include <frc/TimedRobot.h>
#include <frc/Joystick.h>
#include <frc/Spark.h>
#include <networktables/NetworkTableEntry.h>
#include <networktables/NetworkTableInstance.h>
#include <frc/SpeedControllerGroup.h>
#include <frc/drive/DifferentialDrive.h>
#include <frc/Encoder.h>

class Robot : public frc::TimedRobot {
public:
    void RobotInit() override;
    void RobotPeriodic() override;

    void DisabledInit() override;

    void AutonomousInit() override;
    void AutonomousPeriodic() override;

    void TeleopInit() override;
    void TeleopPeriodic() override;

    void TestInit() override;
    void TestPeriodic() override;

private:
    static constexpr double kWheelDiameter = 0.5;
    static constexpr double kEncoderPulsePerRev = 360;

    frc::Joystick m_joystick{0};

    frc::Spark m_leftFrontMotor{1};
    frc::Spark m_rightFrontMotor{2};
    frc::Spark m_leftRearMotor{3};
    frc::Spark m_rightRearMotor{4};

    frc::SpeedControllerGroup m_leftGroup{m_leftFrontMotor, m_leftRearMotor};
    frc::SpeedControllerGroup m_rightGroup{m_rightFrontMotor, m_rightRearMotor};

    frc::DifferentialDrive m_drive{m_leftGroup, m_rightGroup};

    double priorAutoSpeed{0.0};

    nt::NetworkTableEntry m_autoSpeedEntry =
        nt::NetworkTableInstance::GetDefault().GetEntry("/robot/autospeed");
    nt::NetworkTableEntry m_telemetryEntry =
        nt::NetworkTableInstance::GetDefault().GetEntry("/robot/telemetry");

    frc::Encoder m_leftEncoder{0, 1};
    frc::Encoder m_rightEncoder{0, 1};

    std::function<double(void)> m_leftEncoderPosition = [this]() {
        return m_leftEncoder.GetDistance();
    };
    std::function<double(void)> m_leftEncoderRate = [this]() {
        return m_leftEncoder.GetRate();
    };
    std::function<double(void)> m_rightEncoderPosition = [this]() {
        return m_rightEncoder.GetDistance();
    };
    std::function<double(void)> m_rightEncoderRate = [this]() {
        return m_rightEncoder.GetRate();
    };
};
