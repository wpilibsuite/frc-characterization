/**
 * This is a very simple robot program that can be used to send telemetry to
 * the data_logger script to characterize your drivetrain. If you wish to use
 * your actual robot code, you only need to implement the simple logic in the
 * autonomousPeriodic function and change the NetworkTables update rate
 */

package dc;

import java.util.function.Supplier;

import edu.wpi.first.networktables.NetworkTableEntry;
import edu.wpi.first.networktables.NetworkTableInstance;
import edu.wpi.first.wpilibj.Encoder;
import edu.wpi.first.wpilibj.Joystick;
import edu.wpi.first.wpilibj.RobotController;
import edu.wpi.first.wpilibj.Spark;
import edu.wpi.first.wpilibj.SpeedControllerGroup;
import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj.Timer;
import edu.wpi.first.wpilibj.drive.DifferentialDrive;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;

public class Robot extends TimedRobot {

	static private double WHEEL_DIAMETER = 0.5;
	static private double ENCODER_PULSE_PER_REV = 360;

	Joystick stick;
	DifferentialDrive drive;

	Supplier<Double> leftEncoderPosition;
	Supplier<Double> leftEncoderRate;
	Supplier<Double> rightEncoderPosition;
	Supplier<Double> rightEncoderRate;

	NetworkTableEntry autoSpeedEntry = NetworkTableInstance.getDefault().getEntry("/robot/autospeed");
	NetworkTableEntry telemetryEntry = NetworkTableInstance.getDefault().getEntry("/robot/telemetry");

	double priorAutospeed = 0;
	Number[] numberArray = new Number[9];

	@Override
	public void robotInit() {

		stick = new Joystick(0);

		Spark leftFrontMotor = new Spark(1);
		leftFrontMotor.setInverted(false);

		Spark rightFrontMotor = new Spark(2);
		rightFrontMotor.setInverted(false);

		Spark leftRearMotor = new Spark(3);
		leftRearMotor.setInverted(false);

		Spark rightRearMotor = new Spark(4);
		rightRearMotor.setInverted(false);

		
		//
		// Configure drivetrain movement
		//

		SpeedControllerGroup leftGroup = new SpeedControllerGroup(leftFrontMotor, leftRearMotor);
		SpeedControllerGroup rightGroup = new SpeedControllerGroup(rightFrontMotor, rightRearMotor);

		drive = new DifferentialDrive(leftGroup, rightGroup);
		drive.setDeadband(0);

		
		//
		// Configure encoder related functions -- getDistance and getrate should return
		// ft and ft/s
		//
		
		double encoderConstant = (1 / ENCODER_PULSE_PER_REV) * WHEEL_DIAMETER * Math.PI;

		Encoder leftEncoder = new Encoder(0, 1);
		leftEncoder.setDistancePerPulse(encoderConstant);
		leftEncoderPosition = leftEncoder::getDistance;
		leftEncoderRate = leftEncoder::getRate;

		Encoder rightEncoder = new Encoder(0, 1);
		rightEncoder.setDistancePerPulse(encoderConstant);
		rightEncoderPosition = rightEncoder::getDistance;
		rightEncoderRate = rightEncoder::getRate;

		
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
drive.tankDrive(autospeed, autospeed, false);

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

		telemetryEntry.setNumberArray(numberArray);
	}
}