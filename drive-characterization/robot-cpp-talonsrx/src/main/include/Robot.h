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
#include <math.h>

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
    static constexpr int kPIDIdx = 0;

    static constexpr double kEncoderConstant =
        (1 / kEncoderPulsePerRev) * kWheelDiameter * 3.1415926535;

    frc::Joystick m_joystick{0};

    WPI_TalonSRX m_leftFrontMotor{1};
    WPI_TalonSRX m_rightFrontMotor{2};
    WPI_TalonSRX m_leftRearMotor{3};
    WPI_TalonSRX m_rightRearMotor{4};

    nt::NetworkTableEntry m_autoSpeedEntry =
        nt::NetworkTableInstance::GetDefault().GetEntry("/robot/autospeed");
    nt::NetworkTableEntry m_telemetryEntry =
        nt::NetworkTableInstance::GetDefault().GetEntry("/robot/telemetry");

    frc::SpeedControllerGroup m_leftGroup{m_leftFrontMotor, m_leftRearMotor};
    frc::SpeedControllerGroup m_rightGroup{m_rightFrontMotor, m_rightRearMotor};

    frc::DifferentialDrive m_drive{m_leftGroup, m_rightGroup};

    std::function<double(void)> m_leftEncoderPosition = [this]() {
        return m_leftFrontMotor.GetSelectedSensorPosition(kPIDIdx) *
               kEncoderConstant;
    };
    std::function<double(void)> m_leftEncoderRate = [this]() {
        return m_leftFrontMotor.GetSelectedSensorVelocity(kPIDIdx) *
               kEncoderConstant * 10;
    };
    std::function<double(void)> m_rightEncoderPosition = [this]() {
        return m_rightFrontMotor.GetSelectedSensorPosition(kPIDIdx) *
               kEncoderConstant;
    };
    std::function<double(void)> m_rightEncoderRate = [this]() {
        return m_rightFrontMotor.GetSelectedSensorVelocity(kPIDIdx) *
               kEncoderConstant * 10;
    };

    // You only need to uncomment the below lines if you want to characterize
    // wheelbase radius. Otherwise you can leave this area as-is.
    std::function<double(void)> m_gyroAngleRadians = []() {
        return 0.0;
    };

    // Uncomment for KOP gyro
    // Note that the angle from the NavX and all subclasses of Gyro
    // must be negated because getAngle returns a clockwise angle
    // ADXRS450_Gyro m_kopGyro = ADXRS450_Gyro{};
    // std::function<double(void)> m_gyroAngleRadians = [this]() {
    //     return -1 * m_kopGyro.GetAngle() * (180 / M_PI);
    // };

    // Uncomment for Pigeon
    // PigeonIMU m_pigeon{0};
    // std::array<double, 3> m_gyroXYZ{};
    // std::function<double(void)> m_gyroAngleRadians = [this]() {
    //     m_pigeon.GetAccumGyro(m_gyroXYZ.begin());
    //     return m_gyroXYZ[2] * (180 / M_PI);
    // };

    // Uncomment for NavX
    // AHRS m_navx{SPI::Port::kMXP};
    // std::function<double<void> m_gyroAngleRadians = [this]() {
    //     return -1 * m_navx.GetAngle() * (180 / M_PI);
    // };


    double priorAutoSpeed{0.0};
};
