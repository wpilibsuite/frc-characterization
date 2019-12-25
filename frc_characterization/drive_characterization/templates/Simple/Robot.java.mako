/**
* This is a very simple robot program that can be used to send telemetry to
* the data_logger script to characterize your drivetrain. If you wish to use
* your actual robot code, you only need to implement the simple logic in the
* autonomousPeriodic function and change the NetworkTables update rate
*/

package dc;

import java.util.function.Supplier;

import com.ctre.phoenix.motorcontrol.can.WPI_TalonSRX;
import com.ctre.phoenix.motorcontrol.can.WPI_VictorSPX;

import com.ctre.phoenix.sensors.PigeonIMU;
import com.kauailabs.navx.frc.AHRS;
import edu.wpi.first.wpilibj.ADXRS450_Gyro;
import edu.wpi.first.wpilibj.I2C;
import edu.wpi.first.wpilibj.SPI;

import edu.wpi.first.networktables.NetworkTableEntry;
import edu.wpi.first.networktables.NetworkTableInstance;
import edu.wpi.first.wpilibj.Encoder;
import edu.wpi.first.wpilibj.Joystick;
import edu.wpi.first.wpilibj.PWMTalonSRX;
import edu.wpi.first.wpilibj.PWMVictorSPX;
import edu.wpi.first.wpilibj.RobotController;
import edu.wpi.first.wpilibj.Spark;
import edu.wpi.first.wpilibj.SpeedController;
import edu.wpi.first.wpilibj.SpeedControllerGroup;
import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj.Timer;
import edu.wpi.first.wpilibj.Victor;
import edu.wpi.first.wpilibj.VictorSP;
import edu.wpi.first.wpilibj.drive.DifferentialDrive;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;

public class Robot extends TimedRobot {

  static private double WHEEL_DIAMETER = ${diam};
  static private double ENCODER_PULSE_PER_REV = ${ppr} / 4.;

  Joystick stick;
  DifferentialDrive drive;

  Supplier<Double> leftEncoderPosition;
  Supplier<Double> leftEncoderRate;
  Supplier<Double> rightEncoderPosition;
  Supplier<Double> rightEncoderRate;
  Supplier<Double> gyroAngleRadians;

  NetworkTableEntry autoSpeedEntry = NetworkTableInstance.getDefault().getEntry("/robot/autospeed");
  NetworkTableEntry telemetryEntry = NetworkTableInstance.getDefault().getEntry("/robot/telemetry");
  NetworkTableEntry rotateEntry = NetworkTableInstance.getDefault().getEntry("/robot/rotate");

  double priorAutospeed = 0;
  Number[] numberArray = new Number[10];

  @Override
  public void robotInit() {
    if (!isReal()) SmartDashboard.putData(new SimEnabler());

    stick = new Joystick(0);

    ${lcontrollers[0]} leftMotor1 = new ${lcontrollers[0]}(${lports[0]});
    % if linverted[0]:
    leftMotor1.setInverted(true);
    % endif

    ${rcontrollers[0]} rightMotor1 = new ${lcontrollers[0]}(${rports[0]});
    % if rinverted[0]:
    rightMotor1.setInverted(true);
    % endif

    SpeedController[] leftMotors = new SpeedController[${len(lports) - 1}];
    % for port in lports[1:]:
    leftMotors[${loop.index}] = new ${lcontrollers[loop.index+1]}(${port});
    % if linverted[loop.index+1]:
    leftMotors[${loop.index}].setInverted(true);
    % endif
    % endfor

    SpeedController[] rightMotors = new SpeedController[${len(lports) - 1}];
    % for port in rports[1:]:
    rightMotors[${loop.index}] = new ${rcontrollers[loop.index+1]}(${port});
    % if rinverted[loop.index+1]:
    rightMotors[${loop.index}].setInverted(true);
    % endif
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

    SpeedControllerGroup leftGroup = new SpeedControllerGroup(leftMotor1, leftMotors);
    SpeedControllerGroup rightGroup = new SpeedControllerGroup(rightMotor1, rightMotors);

    drive = new DifferentialDrive(leftGroup, rightGroup);
    drive.setDeadband(0);


    //
    // Configure encoder related functions -- getDistance and getrate should return
    // units and units/s
    //

    double encoderConstant = (1 / ENCODER_PULSE_PER_REV) * WHEEL_DIAMETER * Math.PI;

    Encoder leftEncoder = new Encoder(${lencoderports[0]}, ${lencoderports[1]});
    % if lencoderinv:
    leftEncoder.setReverseDirection(true);
    % endif
    leftEncoder.setDistancePerPulse(encoderConstant);
    leftEncoderPosition = leftEncoder::getDistance;
    leftEncoderRate = leftEncoder::getRate;

    % if rencoderports:
    Encoder rightEncoder = new Encoder(${rencoderports[0]}, ${rencoderports[1]});
    % if rencoderinv:
    rightEncoder.setReverseDirection(true);
    % endif
    rightEncoder.setDistancePerPulse(encoderConstant);
    rightEncoderPosition = rightEncoder::getDistance;
    rightEncoderRate = rightEncoder::getRate;
    % else:
    Encoder rightEncoder = leftEncoder;
    % endif

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
    public void disabledPeriodic() {
  }

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
    double motorVolts = battery * Math.abs(priorAutospeed);

    double leftMotorVolts = motorVolts;
    double rightMotorVolts = motorVolts;

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