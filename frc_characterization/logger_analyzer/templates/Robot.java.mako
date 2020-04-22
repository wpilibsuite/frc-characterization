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

// WPI_Talon* imports are needed in case a user has a Pigeon on a Talon
import com.ctre.phoenix.motorcontrol.FeedbackDevice;
import com.ctre.phoenix.motorcontrol.NeutralMode;
import com.ctre.phoenix.motorcontrol.can.WPI_TalonSRX;
import com.ctre.phoenix.motorcontrol.can.WPI_TalonFX;
import com.ctre.phoenix.sensors.PigeonIMU;
import com.kauailabs.navx.frc.AHRS;
import edu.wpi.first.wpilibj.ADXRS450_Gyro;
import edu.wpi.first.wpilibj.AnalogGyro;
import edu.wpi.first.wpilibj.interfaces.Gyro;
import edu.wpi.first.wpilibj.SerialPort;
import edu.wpi.first.wpilibj.I2C;
import edu.wpi.first.wpilibj.SPI;

import com.revrobotics.CANSparkMax;
import com.revrobotics.CANSparkMax.IdleMode;
import com.revrobotics.CANSparkMaxLowLevel.MotorType;
import com.revrobotics.CANEncoder;
import com.revrobotics.EncoderType;

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

import java.util.ArrayList; 

public class Robot extends TimedRobot {

  static private double ENCODER_EDGES_PER_REV = ${epr} / 4.;
  static private int PIDIDX = 0;
  static private int ENCODER_EPR = ${epr};
  static private double GEARING = ${gearing};
  
  % if control == "SparkMax_Brushless" and integrated:
  private double encoderConstant = (1 / GEARING);
  % else:
  private double encoderConstant = (1 / GEARING) * (1 / ENCODER_EDGES_PER_REV);
  % endif

  Joystick stick;
  % if rightports:
  DifferentialDrive drive;
  % else:
    % if control == "Simple":
  SpeedControllerGroup masterMotor;
    % else:
  ${controller[0]} masterMotor;
    % endif
  % endif


  Supplier<Double> leftEncoderPosition;
  Supplier<Double> leftEncoderRate;
  Supplier<Double> rightEncoderPosition;
  Supplier<Double> rightEncoderRate;
  Supplier<Double> gyroAngleRadians;

  NetworkTableEntry autoSpeedEntry = NetworkTableInstance.getDefault().getEntry("/robot/autospeed");
  NetworkTableEntry telemetryEntry = NetworkTableInstance.getDefault().getEntry("/robot/telemetry");
  NetworkTableEntry rotateEntry = NetworkTableInstance.getDefault().getEntry("/robot/rotate");

  String data = "";
  
  int counter = 0;
  double startTime = 0;
  double priorAutospeed = 0;

  public Robot() {
    super(.01);
  }

  public enum Sides {
    LEFT,
    RIGHT,
    SLAVE
  }

  // TODO add a method to invert encoders for motor:

  // methods to create and setup motors (reduce redundancy)
  % for motor in list(dict.fromkeys(controller + rightcontroller)):
  public ${motor} setup${motor}(int port, Sides side, boolean inverted) {
    // create new motor and set neutral modes (if needed)
    % if "SparkMax" not in control:
    ${motor} motor = new ${motor}(port);
        % if control == "Talon":
    // setup talon
    motor.setNeutralMode(NeutralMode.Brake);
        % endif    
    % else:
          % if "Brushed" in control:
    // setup Brushed spark
    CANSparkMax motor = new CANSparkMax(port, MotorType.kBrushed);
          % else:
    // setup Brushless spark
    CANSparkMax motor = new CANSparkMax(port, MotorType.kBrushless);
          % endif
    motor.setIdleMode(IdleMode.kBrake);
           
    % endif
    motor.setInverted(inverted);
    
    // setup encoder if motor isn't a slave
    if (side != Sides.SLAVE) {
    % if "SparkMax" not in control:
        
      % if control == "Talon":
      motor.configSelectedFeedbackSensor(
          % if controller[0] == "WPI_TalonFX":
            FeedbackDevice.IntegratedSensor,
          % else:
            FeedbackDevice.QuadEncoder,
          % endif
            PIDIDX, 10
      );
      % else:
      
      Encoder encoder;
      % endif
            
    % else:
      % if integrated and "Brushless" in control:
    CANEncoder encoder = motor.getEncoder();
      % else:
    CANEncoder encoder = motor.getEncoder(EncoderType.kQuadrature, ENCODER_EPR);
      % endif
    % endif



    switch (side) {
      // setup encoder and data collecting methods

      % if rightports: #SPARK MAX DOESN"T BRUSHLESS DOESN"T LIKE INVERTING
      case RIGHT:
        // set right side methods = encoder methods

        % if "SparkMax" not in control:

          % if control == "Talon":
          
        motor.setSensorPhase(${str(rencoderinv).lower()});
          
          
        
        rightEncoderPosition = ()
          -> motor.getSelectedSensorPosition(PIDIDX) * encoderConstant;
        rightEncoderRate = ()
          -> motor.getSelectedSensorVelocity(PIDIDX) * encoderConstant *
               10;

          % else:
        
        encoder = new Encoder(${rencoderports[0]}, ${rencoderports[1]});
        encoder.setReverseDirection(${str(rencoderinv).lower()});

        encoder.setDistancePerPulse(encoderConstant);
        rightEncoderPosition = encoder::getDistance;
        rightEncoderRate = encoder::getRate;

          % endif
        % else:
          % if "Brushless" not in control:
        encoder.setInverted(${str(rencoderinv).lower()});
          % endif
        rightEncoderPosition = ()
          -> encoder.getPosition() * encoderConstant;
        rightEncoderRate = ()
          -> encoder.getVelocity() * encoderConstant / 60.;

        % endif

        break;
      % endif
      case LEFT:
         % if "SparkMax" not in control:

          % if control == "Talon":
        motor.setSensorPhase(${str(encoderinv).lower()});
        
        leftEncoderPosition = ()
          -> motor.getSelectedSensorPosition(PIDIDX) * encoderConstant;
        leftEncoderRate = ()
          -> motor.getSelectedSensorVelocity(PIDIDX) * encoderConstant *
               10;

          % else:
        encoder = new Encoder(${encoderports[0]}, ${encoderports[1]});
        encoder.setReverseDirection(${str(encoderinv).lower()});
        encoder.setDistancePerPulse(encoderConstant);
        leftEncoderPosition = encoder::getDistance;
        leftEncoderRate = encoder::getRate;

          % endif
        % else:
        % if "Brushless" not in control:
        encoder.setInverted(${str(encoderinv).lower()});
          % endif
        leftEncoderPosition = ()
          -> encoder.getPosition() * encoderConstant;
        leftEncoderRate = ()
          -> encoder.getVelocity() * encoderConstant / 60.;

        % endif

        break;
      default:
        // probably do nothing
        break;

      }
    
    }
    

    return motor;

  }
  % endfor  

  @Override
  public void robotInit() {
    if (!isReal()) SmartDashboard.putData(new SimEnabler());

    stick = new Joystick(0);
    
    // create left motor
    ${controller[0]} leftMotor = setup${controller[0]}(${ports[0]}, Sides.LEFT, ${str(inverted[0]).lower()});

    % if control != "Simple":
      % for port in ports[1:]: # add slaves if there are any
    ${controller[loop.index + 1]} leftSlaveID${port} = setup${controller[loop.index + 1]}(${port}, Sides.SLAVE, ${str(inverted[loop.index + 1]).lower()});
    leftSlaveID${port}.follow(leftMotor);
      % endfor
    % else:
      % if len(ports) > 1:
    ArrayList<SpeedController> leftMotors = new ArrayList<SpeedController>();
      % for port in ports[1:]:
    leftMotors.add(setup${controller[loop.index + 1]}(${port}, Sides.SLAVE, ${str(inverted[loop.index + 1]).lower()}));
      % endfor
    SpeedController[] leftMotorControllers = new SpeedController[leftMotors.size()];
    leftMotorControllers = leftMotors.toArray(leftMotorControllers);
    SpeedControllerGroup leftGroup = new SpeedControllerGroup(leftMotor, leftMotorControllers);
      % else:
    SpeedControllerGroup leftGroup = new SpeedControllerGroup(leftMotor);
      % endif
    % endif

    % if rightports: # setup right side (if it exists)
    ${rightcontroller[0]} rightMotor = setup${rightcontroller[0]}(${rightports[0]}, Sides.RIGHT, ${str(rightinverted[0]).lower()});
      % if control != "Simple":
        % for port in rightports[1:]:
    ${rightcontroller[loop.index + 1]} rightSlaveID${port} = setup${rightcontroller[loop.index + 1]}(${port}, Sides.SLAVE, ${str(rightinverted[loop.index + 1]).lower()});
    rightSlaveID${port}.follow(rightMotor);  
        % endfor
    drive = new DifferentialDrive(leftMotor, rightMotor);
      % else:
        % if rightports:
    ArrayList<SpeedController> rightMotors = new ArrayList<SpeedController>();
          % for port in rightports[1:]:
    rightMotors.add(setup${rightcontroller[loop.index + 1]}(${port}, Sides.SLAVE, ${str(rightinverted[loop.index + 1]).lower()}));
          % endfor
    SpeedController[] rightMotorControllers = new SpeedController[rightMotors.size()];
    rightMotorControllers = rightMotors.toArray(rightMotorControllers);
    SpeedControllerGroup rightGroup = new SpeedControllerGroup(rightMotor, rightMotorControllers);
        % else:
    SpeedControllerGroup rightGroup = new SpeedControllerGroup(rightMotor);
        % endif
    drive = new DifferentialDrive(leftGroup, rightGroup);
      % endif
    drive.setDeadband(0);
    % else:
    rightEncoderPosition = leftEncoderPosition;
    rightEncoderRate = leftEncoderRate;
      % if control != "Simple":
    masterMotor = leftMotor;
      % else:
    masterMotor = new SpeedControllerGroup(leftMotor, leftMotorControllers);
      % endif
    % endif
    //
    // Configure gyro
    //

    % if gyro:
      // Note that the angle from the NavX and all implementors of wpilib Gyro
      // must be negated because getAngle returns a clockwise positive angle
      % if gyro == "ADXRS450":
    Gyro gyro = new ADXRS450_Gyro(${gyroport});
    gyroAngleRadians = () -> -1 * Math.toRadians(gyro.getAngle());
      % elif gyro == "AnalogGyro":
    Gyro gyro = new AnalogGyro(${gyroport});
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
    % endif
    // Set the update rate instead of using flush because of a ntcore bug
    // -> probably don't want to do this on a robot in competition
    NetworkTableInstance.getDefault().setUpdateRate(0.010);
  }

  @Override
  public void disabledInit() {
    System.out.println("Robot disabled");
    % if rightports:
    drive.tankDrive(0, 0);
    % else:
    masterMotor.set(0);
    % endif
    double elapsedTime = Timer.getFPGATimestamp() - startTime;
    System.out.println("Robot disabled");
    System.out.println("Collected : " + counter + " in " + elapsedTime + " seconds");
    telemetryEntry.setString(data);
    data = "";
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
    % if rightports:
    drive.arcadeDrive(-stick.getY(), stick.getX());
    % else:
    masterMotor.set(-stick.getY());
    % endif
  }

  @Override
  public void autonomousInit() {
    System.out.println("Robot in autonomous mode");
    startTime = Timer.getFPGATimestamp();
    counter = 0;
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
    % if rightports:
    drive.tankDrive(
      (rotateEntry.getBoolean(false) ? -1 : 1) * autospeed, autospeed,
      false
    );
    % else:
    masterMotor.set(autospeed);
    % endif
    Number[] numberArray = new Number[10];

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

    // Add data to a string that is uploaded to NT
    for (Number num : numberArray) {
      data += num + ", ";
    }
    counter++;
  }
}