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

import com.ctre.phoenix.motorcontrol.FeedbackDevice;
import com.ctre.phoenix.motorcontrol.NeutralMode;
import com.ctre.phoenix.motorcontrol.can.WPI_TalonSRX;

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

	// The total gear reduction between the encoder and the arm
	static private double GEARING = 1;
	// The offset of encoder zero from horizontal, in degrees.
	// It is CRUCIAL that this be set correctly, or the characterization will not work!
	static private double OFFSET = 0;
	static private double ENCODER_PULSE_PER_REV = 360;
	static private int PIDIDX = 0;

	Joystick stick;

	WPI_TalonSRX armMotor;

	Supplier<Double> encoderPosition;
	Supplier<Double> encoderRate;

	NetworkTableEntry autoSpeedEntry = NetworkTableInstance.getDefault().getEntry("/robot/autospeed");
	NetworkTableEntry telemetryEntry = NetworkTableInstance.getDefault().getEntry("/robot/telemetry");

	double priorAutospeed = 0;
	Number[] numberArray = new Number[6];

	@Override
	public void robotInit() {

		stick = new Joystick(0);

		armMotor = new WPI_TalonSRX(1);
		armMotor.setInverted(false);
		armMotor.setSensorPhase(false);
		armMotor.setNeutralMode(NeutralMode.Brake);

		//
		// Configure encoder related functions -- getDistance and getrate should return
		// degrees and degrees/sec
		//

		double encoderConstant = (1 / ENCODER_PULSE_PER_REV) / GEARING * 360.;

		armMotor.configSelectedFeedbackSensor(FeedbackDevice.QuadEncoder, PIDIDX, 10);
		encoderPosition = () -> armMotor.getSelectedSensorPosition(PIDIDX) * encoderConstant + OFFSET;
		encoderRate = () -> armMotor.getSelectedSensorVelocity(PIDIDX) * encoderConstant * 10;

		// Reset encoders
		armMotor.setSelectedSensorPosition(0);

		// Set the update rate instead of using flush because of a ntcore bug
		// -> probably don't want to do this on a robot in competition
		NetworkTableInstance.getDefault().setUpdateRate(0.010);
	}

	@Override
	public void disabledInit() {
		System.out.println("Robot disabled");
		armMotor.set(0);
	}

	@Override
	public void disabledPeriodic() {
	}

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
		armMotor.set(-stick.getY());
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

		double motorVolts = armMotor.getMotorOutputVoltage();

		// Retrieve the commanded speed from NetworkTables
		double autospeed = autoSpeedEntry.getDouble(0);
		priorAutospeed = autospeed;

		// command motors to do things
		armMotor.set(autospeed);

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
