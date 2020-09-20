/**
 * This is a very simple robot program that can be used to send telemetry to
 * the data_logger script to characterize your drivetrain. If you wish to use
 * your actual robot code, you only need to implement the simple logic in the
 * autonomousPeriodic function and change the NetworkTables update rate
 */

package dc;

import java.util.function.Supplier;

import com.revrobotics.CANSparkMax;
import com.revrobotics.CANSparkMax.IdleMode;
import com.revrobotics.CANSparkMaxLowLevel.MotorType;
import com.revrobotics.CANEncoder;
import com.revrobotics.EncoderType;

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

  // The offset of encoder zero from horizontal, in degrees.
  // It is CRUCIAL that this be set correctly, or the characterization will not
  // work!
  static private int ENCODER_EPR = ${epr};
  static private double PULLEY_DIAMETER = ${diam};
  static private double GEARING = ${gearing};
  static private int PIDIDX = 0;

  Joystick stick;

  CANSparkMax elevatorLeader;

  Supplier<Double> encoderPosition;
  Supplier<Double> encoderRate;

  NetworkTableEntry autoSpeedEntry =
      NetworkTableInstance.getDefault().getEntry("/robot/autospeed");
  NetworkTableEntry telemetryEntry =
      NetworkTableInstance.getDefault().getEntry("/robot/telemetry");

  double priorAutospeed = 0;
  Number[] numberArray = new Number[6];

  @Override
  public void robotInit() {
    if (!isReal()) SmartDashboard.putData(new SimEnabler());

    stick = new Joystick(0);

    elevatorLeader = new CANSparkMax(${ports[0]}, MotorType.kBrushed);
    % if inverted[0]:
    elevatorLeader.setInverted(true);
    % else:
    elevatorLeader.setInverted(false);
    % endif
    elevatorLeader.setIdleMode(IdleMode.kBrake);

    % for port in ports[1:]:
    CANSparkMax elevatorFollower${loop.index} = new CANSparkMax(${port}, MotorType.kBrushed);
    % if inverted[loop.index+1]:
    elevatorFollower${loop.index}.setInverted(true);
    % else:
    elevatorFollower${loop.index}.setInverted(false);
    % endif
    elevatorFollower${loop.index}.setIdleMode(IdleMode.kBrake);
    elevatorFollower${loop.index}.follow(elevatorLeader);
    % endfor

    //
    // Configure encoder related functions -- getDistance and getrate should
    // return units and units/sec
    //

    double encoderConstant = (1 / GEARING) * PULLEY_DIAMETER * Math.PI;

    CANEncoder encoder = elevatorLeader.getEncoder(EncoderType.kQuadrature, ENCODER_EPR);

    % if encoderinv:
    encoder.setInverted(true);
    % endif

    encoderPosition = 
        () -> encoder.getPosition() * encoderConstant;
    encoderRate =
        () -> encoder.getVelocity() * encoderConstant / 60.;

    // Reset encoders
    encoder.setPosition(0);

    // Set the update rate instead of using flush because of a ntcore bug
    // -> probably don't want to do this on a robot in competition
    NetworkTableInstance.getDefault().setUpdateRate(0.010);
  }

  @Override
  public void disabledInit() {
    System.out.println("Robot disabled");
    elevatorLeader.set(0);
  }

  @Override
  public void disabledPeriodic() {}

  @Override
  public void robotPeriodic() {
    // feedback for users, but not used by the control program
    SmartDashboard.putNumber("encoder_pos", encoderPosition.get());
    SmartDashboard.putNumber("encoder_rate", encoderRate.get());
  }

  @Override
  public void teleopInit() {
    System.out.println("Robot in operator control mode");
  }

  @Override
  public void teleopPeriodic() {
    elevatorLeader.set(-stick.getY());
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

    double position = encoderPosition.get();
    double rate = encoderRate.get();

    double battery = RobotController.getBatteryVoltage();

    double motorVolts = elevatorLeader.getBusVoltage() * elevatorLeader.getAppliedOutput();

    // Retrieve the commanded speed from NetworkTables
    double autospeed = autoSpeedEntry.getDouble(0);
    priorAutospeed = autospeed;

    // command motors to do things
    elevatorLeader.set(autospeed);

    // send telemetry data array back to NT
    numberArray[0] = now;
    numberArray[1] = battery;
    numberArray[2] = autospeed;
    numberArray[3] = motorVolts;
    numberArray[4] = position;
    numberArray[5] = rate;
    telemetryEntry.setNumberArray(numberArray);
  }
}
