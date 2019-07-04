/*----------------------------------------------------------------------------*/
/* Copyright (c) 2018 FIRST. All Rights Reserved.                             */
/* Open Source Software - may be modified and shared by FRC teams. The code   */
/* must be accompanied by the FIRST BSD license file in the root directory of */
/* the project.                                                               */
/*----------------------------------------------------------------------------*/

#pragma once

#include <frc/TimedRobot.h>
#include <frc/Joystick.h>
#include <ctre/Phoenix.h>
#include <networktables/NetworkTableEntry.h>
#include <networktables/NetworkTableInstance.h>
#include <frc/drive/DifferentialDrive.h>
#include <frc/SpeedControllerGroup.h>

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
    // The total gear reduction between the encoder and the arm
    static constexpr double kGearing = 1;

    // The offset of encoder zero from horizontal, in degrees.
    // It is CRUCIAL that this be set correctly, or the characterization will
    // not work!
    static constexpr double kOffset = 0;

    static constexpr double kEncoderPulsePerRev = 360;
    static constexpr int kPIDIdx = 0;

    static constexpr double kEncoderConstant =
        (1 / kEncoderPulsePerRev) / kGearing * 360.;

    frc::Joystick m_joystick{0};

    WPI_TalonSRX m_armMotor{1};

    nt::NetworkTableEntry m_autoSpeedEntry =
        nt::NetworkTableInstance::GetDefault().GetEntry("/robot/autospeed");
    nt::NetworkTableEntry m_telemetryEntry =
        nt::NetworkTableInstance::GetDefault().GetEntry("/robot/telemetry");

    std::function<double(void)> m_encoderPosition = [this]() {
        return m_armMotor.GetSelectedSensorPosition(kPIDIdx) *
                   kEncoderConstant +
               kOffset;
    };
    std::function<double(void)> m_encoderRate = [this]() {
        return m_armMotor.GetSelectedSensorVelocity(kPIDIdx) *
               kEncoderConstant * 10;
    };

    double priorAutoSpeed{0.0};
};
