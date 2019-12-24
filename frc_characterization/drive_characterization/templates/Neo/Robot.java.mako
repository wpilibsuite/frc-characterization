/**
 * This is a very simple robot program that can be used to send telemetry to
 * the data_logger script to characterize your drivetrain. If you wish to use
 * your actual robot code, you only need to implement the simple logic in the
 * autonomousPeriodic function and change the NetworkTables update rate
 *
 * This program assumes that you are using TalonSRX motor controllers and that
 * the drivetrain encoders are attached to the TalonSRX
 */

package dc;

import java.util.function.Supplier;

import com.revrobotics.CANEncoder;
import com.revrobotics.CANSparkMax;
import com.revrobotics.CANSparkMax.IdleMode;
import com.revrobotics.CANSparkMaxLowLevel.MotorType;

import com.ctre.phoenix.sensors.PigeonIMU;
import com.kauailabs.navx.frc.AHRS;
import edu.wpi.first.wpilibj.ADXRS450_Gyro;
import edu.wpi.first.wpilibj.I2C;
import edu.wpi.first.wpilibj.SPI;

import edu.wpi.first.networktables.NetworkTableEntry;
import edu.wpi.first.networktables.NetworkTableInstance;
import edu.wpi.first.wpilibj.Joystick;
import edu.wpi.first.wpilibj.RobotController;
import edu.wpi.first.wpilibj.SpeedControllerGroup;
import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj.Timer;
import edu.wpi.first.wpilibj.drive.DifferentialDrive;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;

public class Robot extends TimedRobot {

  static private double WHEEL_DIAMETER = ${diam};
  static private double GEARING = ${gearing};
  static private int PIDIDX = 0;

  Joystick stick;
  DifferentialDrive drive;

  CANSparkMax leftMaster;
  CANSparkMax rightMaster;

  CANEncoder leftEncoder;
  CANEncoder rightEncoder;

  Supplier<Double> leftEncoderPosition;
  Supplier<Double> leftEncoderRate;
  Supplier<Double> rightEncoderPosition;
  Supplier<Double> rightEncoderRate;
  Supplier<Double> gyroAngleRadians;

  NetworkTableEntry autoSpeedEntry =
      NetworkTableInstance.getDefault().getEntry("/robot/autospeed");
  NetworkTableEntry telemetryEntry =
      NetworkTableInstance.getDefault().getEntry("/robot/telemetry");
  NetworkTableEntry rotateEntry =
    NetworkTableInstance.getDefault().getEntry("/robot/rotate");

  double priorAutospeed = 0;
  Number[] numberArray = new Number[10];

  @Override
  public void robotInit() {
    if (!isReal()) SmartDashboard.putData(new SimEnabler());

    stick = new Joystick(0);

    leftMaster = new CANSparkMax(${lports[0]}, MotorType.kBrushless);
    % if linverted[0]:
    leftMaster.setInverted(true);
    % else:
    leftMaster.setInverted(false);
    % endif
    leftMaster.setIdleMode(IdleMode.kBrake);

    leftEncoder = leftMaster.getEncoder();

    rightMaster = new CANSparkMax(${rports[0]}, MotorType.kBrushless);
    % if linverted[0]:
    rightMaster.setInverted(true);
    % else:
    rightMaster.setInverted(false);
    % endif
    rightMaster.setIdleMode(IdleMode.kBrake);

    rightEncoder = rightMaster.getEncoder();

    % for port in lports[1:]:
    CANSparkMax leftSlave${loop.index} = new CANSparkMax(${port}, MotorType.kBrushless);
    % if linverted[loop.index+1]:
    leftSlave${loop.index}.follow(leftMaster, true);
    % else:
    leftSlave${loop.index}.follow(leftMaster);
    % endif
    leftSlave${loop.index}.setIdleMode(IdleMode.kBrake);
    % endfor

    % for port in rports[1:]:
    CANSparkMax rightSlave${loop.index} = new CANSparkMax(${port}, MotorType.kBrushless);
    % if rinverted[loop.index+1]:
    rightSlave${loop.index}.follow(rightMaster, true);
    % else:
    rightSlave${loop.index}.follow(rightMaster);
    % endif
    rightSlave${loop.index}.setIdleMode(IdleMode.kBrake);
    % endfor

    //
    // Configure gyro
    //

    // Note that the angle from the NavX and all implementors of wpilib Gyro
    // must be negated because getAngle returns a clockwise positive angle
    % if gyro == "ADXRS450":
    Gyro gyro = new ADXRS450_Gyro(${gyroport});
    gyroAngleRadians = () -> -1 * Math.toRadians(gyro.getAngle());
    % elif gyro == "NavX":
    AHRS navx = new AHRS(${gyroport});
    gyroAngleRadians = () -> -1 * Math.toRadians(navx.getAngle());
    % elif gyro == "Pigeon":
    // Uncomment for Pigeon
    PigeonIMU pigeon = new PigeonIMU(${gyroport});
    gyroAngleRadians = () -> {
      // Allocating a new array every loop is bad but concise
      double[] xyz = new double[3];
      pigeon.getAccumGyro(xyz);
      return Math.toRadians(xyz[2]);
    };
    % else:
    gyroAngleRadians = () -> 0.0;
    % endif

    //
    // Configure drivetrain movement
    //

    drive = new DifferentialDrive(leftMaster, rightMaster);

    drive.setDeadband(0);

    //
    // Configure encoder related functions -- getDistance and getrate should
    // return units and units/s
    //

    double encoderConstant =
        (1 / GEARING) * WHEEL_DIAMETER * Math.PI;

    leftEncoderPosition = ()
        -> leftEncoder.getPosition() * encoderConstant;
    leftEncoderRate = ()
        -> leftEncoder.getVelocity() * encoderConstant / 60.;

    rightEncoderPosition = ()
        -> rightEncoder.getPosition() * encoderConstant;
    rightEncoderRate = ()
        -> rightEncoder.getVelocity() * encoderConstant / 60.;

    // Reset encoders
    leftEncoder.setPosition(0);
    rightEncoder.setPosition(0);

    // Set the update rate instead of using flush because of a ntcore bug
    // -> probably don't want to do this on a robot in competition
    NetworkTableInstance.getDefault().setUpdateRate(0.010);
  }

  @Override
  public void disabledInit() {
    System.out.println("Robot disabled");
    drive.tankDrive(0, 0);
  }

  @Override
  public void disabledPeriodic() {}

  @Override
  public void robotPeriodic() {
    // feedback for users, but not used by the control program
    SmartDashboard.putNumber("l_encoder_pos", leftEncoderPosition.get());
    SmartDashboard.putNumber("l_encoder_rate", leftEncoderRate.get());
    SmartDashboard.putNumber("r_encoder_pos", rightEncoderPosition.get());
    SmartDashboard.putNumber("r_encoder_rate", rightEncoderRate.get());
  }

  @Override
  public void teleopInit() {
    System.out.println("Robot in operator control mode");
  }

  @Override
  public void teleopPeriodic() {
    drive.arcadeDrive(-stick.getY(), stick.getX());
  }

  @Override
  public void autonomousInit() {
    System.out.println("Robot in autonomous mode");
  }

  /**
   * If you wish to just use your own robot program to use with the data logging
   * program, you only need to copy/paste the logic below into your code and
   * ensure it gets called periodically in autonomous mode
   *
   * Additionally, you need to set NetworkTables update rate to 10ms using the
   * setUpdateRate call.
   */
  @Override
  public void autonomousPeriodic() {

    // Retrieve values to send back before telling the motors to do something
    double now = Timer.getFPGATimestamp();

    double leftPosition = leftEncoderPosition.get();
    double leftRate = leftEncoderRate.get();

    double rightPosition = rightEncoderPosition.get();
    double rightRate = rightEncoderRate.get();

    double battery = RobotController.getBatteryVoltage();

    double leftMotorVolts = leftMaster.getBusVoltage() * leftMaster.getAppliedOutput();
    double rightMotorVolts = rightMaster.getBusVoltage() * rightMaster.getAppliedOutput();

    // Retrieve the commanded speed from NetworkTables
    double autospeed = autoSpeedEntry.getDouble(0);
    priorAutospeed = autospeed;

    // command motors to do things
    drive.tankDrive(
      (rotateEntry.getBoolean(false) ? -1 : 1) * autospeed, autospeed,
      false
    );

    // send telemetry data array back to NT
    numberArray[0] = now;
    numberArray[1] = battery;
    numberArray[2] = autospeed;
    numberArray[3] = leftMotorVolts;
    numberArray[4] = rightMotorVolts;
    numberArray[5] = leftPosition;
    numberArray[6] = rightPosition;
    numberArray[7] = leftRate;
    numberArray[8] = rightRate;
    numberArray[9] = gyroAngleRadians.get();

    telemetryEntry.setNumberArray(numberArray);
  }
}
