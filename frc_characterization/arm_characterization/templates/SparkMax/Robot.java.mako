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
  static private int ENCODER_PPR = ${ppr};
  static private double OFFSET = ${offset};
  static private double GEARING = ${gearing};
  static private int PIDIDX = 0;

  Joystick stick;

  CANSparkMax armMaster;

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

    armMaster = new CANSparkMax(${ports[0]}, MotorType.kBrushed);
    % if inverted[0]:
    armMaster.setInverted(true);
    % else:
    armMaster.setInverted(false);
    % endif
    armMaster.setIdleMode(IdleMode.kBrake);

    % for port in ports[1:]:
    CANSparkMax armSlave${loop.index} = new CANSparkMax(${port}, MotorType.kBrushed);
    % if inverted[loop.index+1]:
    armSlave${loop.index}.setInverted(true);
    % else:
    armSlave${loop.index}.setInverted(false);
    % endif
    armSlave${loop.index}.setIdleMode(IdleMode.kBrake);
    armSlave${loop.index}.follow(armMaster);
    % endfor

    //
    // Configure encoder related functions -- getDistance and getrate should
    // return units and units/sec
    //

    % if units == 'Degrees':
    double encoderConstant = (1 / GEARING) * 360.;
    % elif units == 'Radians':
    double encoderConstant = (1 / GEARING) * 2. * Math.PI;
    % elif units == 'Rotations':
    double encoderConstant = (1 / GEARING);
    % else:
    double encoderConstant = 1;
    % endif

    CANEncoder encoder = armMaster.getEncoder(EncoderType.kQuadrature, ENCODER_PPR);

    % if encoderinv:
    encoder.setInverted(true);
    % endif

    encoderPosition = 
        () -> encoder.getPosition() * encoderConstant +
               OFFSET;
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
    armMaster.set(0);
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
    armMaster.set(-stick.getY());
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

    double motorVolts = armMaster.getBusVoltage() * armMaster.getAppliedOutput();

    // Retrieve the commanded speed from NetworkTables
    double autospeed = autoSpeedEntry.getDouble(0);
    priorAutospeed = autospeed;

    // command motors to do things
    armMaster.set(autospeed);

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
