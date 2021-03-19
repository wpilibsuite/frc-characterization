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

import com.playingwithfusion.CANVenom;

import com.revrobotics.CANSparkMax;
import com.revrobotics.CANSparkMax.IdleMode;
import com.revrobotics.CANSparkMaxLowLevel.MotorType;
import com.revrobotics.CANEncoder;
import com.revrobotics.EncoderType;
import com.revrobotics.AlternateEncoderType;

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
import edu.wpi.first.wpilibj.livewindow.LiveWindow;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;

import java.util.ArrayList; 

public class Robot extends TimedRobot {

  static private double ENCODER_EDGES_PER_REV = ${encoderEPR};
  static private int PIDIDX = 0;
  static private int ENCODER_EPR = ${encoderEPR};
  static private double GEARING = ${gearing};
  
  % if controlType == "SparkMax":
  private double encoderConstant = (1 / GEARING);
  % else:
  private double encoderConstant = (1 / GEARING) * (1 / ENCODER_EDGES_PER_REV);
  % endif

  Joystick stick;
  % if rightMotorPorts:
  DifferentialDrive drive;
  % else:
    % if controlType == "Simple":
  SpeedControllerGroup leaderMotor;
    % else:
  ${controllerTypes[0]} leaderMotor;
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

  double[] numberArray = new double[10];
  ArrayList<Double> entries = new ArrayList<Double>();
  public Robot() {
    super(.005);
    LiveWindow.disableAllTelemetry();
  }

  public enum Sides {
    LEFT,
    RIGHT,
    FOLLOWER
  }

  // methods to create and setup motors (reduce redundancy)
  % for motor in list(dict.fromkeys(controllerTypes + rightControllerTypes)):
  public ${motor} setup${motor}(int port, Sides side, boolean inverted) {
    // create new motor and set neutral modes (if needed)
    % if controlType != "SparkMax":
    ${motor} motor = new ${motor}(port);
        % if controlType == "CTRE":
    // setup talon
    motor.configFactoryDefault();
    motor.setNeutralMode(NeutralMode.Brake);
        % endif    
    % else:
          % if brushed:
    // setup Brushed spark
    CANSparkMax motor = new CANSparkMax(port, MotorType.kBrushed);
          % else:
    // setup Brushless spark
    CANSparkMax motor = new CANSparkMax(port, MotorType.kBrushless);
          % endif
    motor.restoreFactoryDefaults(); 
    motor.setIdleMode(IdleMode.kBrake);  
    % endif
    motor.setInverted(inverted);
    
    // setup encoder if motor isn't a follower
    if (side != Sides.FOLLOWER) {
    
    % if encoderPorts or controlType == "Simple":
      Encoder encoder;
    % else:
      
      % if controlType == "CTRE":
      motor.configSelectedFeedbackSensor(
          % if controllerTypes[0] == "WPI_TalonFX":
            FeedbackDevice.IntegratedSensor,
          % else:
            FeedbackDevice.QuadEncoder,
          % endif
            PIDIDX, 10
      );    
      % elif controlType == "SparkMax":
        % if not useDataPort:
          % if not brushed:
      CANEncoder encoder = motor.getEncoder();
          % else:
      CANEncoder encoder = motor.getEncoder(EncoderType.kQuadrature, ENCODER_EPR);
          % endif
        % else:
      CANEncoder encoder = motor.getAlternateEncoder(AlternateEncoderType.kQuadrature, ENCODER_EPR);
        % endif
      % endif
    % endif



    switch (side) {
      // setup encoder and data collecting methods

      % if rightMotorPorts: #SPARK MAX DOESN"T BRUSHLESS DOESN"T LIKE INVERTING
      case RIGHT:
        // set right side methods = encoder methods

        % if encoderPorts or controlType == "Simple":
        encoder = new Encoder(${rightEncoderPorts[0]}, ${rightEncoderPorts[1]});
        encoder.setReverseDirection(${str(rightEncoderInverted).lower()});

        encoder.setDistancePerPulse((double) encoderConstant / 4);
        rightEncoderPosition = encoder::getDistance;
        rightEncoderRate = encoder::getRate;
        % else:
          % if controlType == "CTRE":
          
        motor.setSensorPhase(${str(rightEncoderInverted).lower()});
        rightEncoderPosition = ()
          -> motor.getSelectedSensorPosition(PIDIDX) * encoderConstant;
        rightEncoderRate = ()
          -> motor.getSelectedSensorVelocity(PIDIDX) * encoderConstant *
               10;          
          %elif controlType == "Venom":

        rightEncoderPosition = ()
          -> motor.getPosition();     // Revolutions
        rightEncoderRate = ()
          -> motor.getSpeed() / 60.;  // Convert RPM to Rev/second
          % else:

            % if brushed or useDataPort:
        encoder.setInverted(${str(rightEncoderInverted).lower()});
            % endif
        rightEncoderPosition = ()
          -> encoder.getPosition() * encoderConstant;
        rightEncoderRate = ()
          -> encoder.getVelocity() * encoderConstant / 60.;
          % endif
        % endif

        break;
      % endif
      case LEFT:
        % if encoderPorts or controlType == "Simple":
        encoder = new Encoder(${encoderPorts[0]}, ${encoderPorts[1]});
        encoder.setReverseDirection(${str(encoderInverted).lower()});
        encoder.setDistancePerPulse((double) encoderConstant / 4);
        leftEncoderPosition = encoder::getDistance;
        leftEncoderRate = encoder::getRate;

        % else:
          % if controlType == "CTRE":
        motor.setSensorPhase(${str(encoderInverted).lower()});
        
        leftEncoderPosition = ()
          -> motor.getSelectedSensorPosition(PIDIDX) * encoderConstant;
        leftEncoderRate = ()
          -> motor.getSelectedSensorVelocity(PIDIDX) * encoderConstant *
               10;
        
          %elif controlType == "Venom":

        leftEncoderPosition = ()
          -> motor.getPosition();     // Revolutions
        leftEncoderRate = ()
          -> motor.getSpeed() / 60.;  // Convert RPM to Rev/second
          % else:
            % if brushed or useDataPort:
        encoder.setInverted(${str(encoderInverted).lower()});
            % endif
        leftEncoderPosition = ()
          -> encoder.getPosition() * encoderConstant;
        leftEncoderRate = ()
          -> encoder.getVelocity() * encoderConstant / 60.;
          % endif
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
    ${controllerTypes[0]} leftMotor = setup${controllerTypes[0]}(${motorPorts[0]}, Sides.LEFT, ${str(motorsInverted[0]).lower()});

    % if controlType != "Simple":
      % for port in motorPorts[1:]: # add followers if there are any
        % if controlType != "SparkMax":
    ${controllerTypes[loop.index + 1]} leftFollowerID${port} = setup${controllerTypes[loop.index + 1]}(${port}, Sides.FOLLOWER, ${str(motorsInverted[loop.index + 1]).lower()});
    leftFollowerID${port}.follow(leftMotor);
        % else:
    CANSparkMax leftFollowerID${port} = setupCANSparkMax(${port}, Sides.FOLLOWER, ${str(motorsInverted[loop.index + 1]).lower()});
    leftFollowerID${port}.follow(leftMotor, ${str(motorsInverted[loop.index + 1]).lower()});
        
    
        % endif
      % endfor
    % else:
      % if len(motorPorts) > 1:
    ArrayList<SpeedController> leftMotors = new ArrayList<SpeedController>();
      % for port in motorPorts[1:]:
    leftMotors.add(setup${controllerTypes[loop.index + 1]}(${port}, Sides.FOLLOWER, ${str(motorsInverted[loop.index + 1]).lower()}));
      % endfor
    SpeedController[] leftMotorControllers = new SpeedController[leftMotors.size()];
    leftMotorControllers = leftMotors.toArray(leftMotorControllers);
    SpeedControllerGroup leftGroup = new SpeedControllerGroup(leftMotor, leftMotorControllers);
      % else:
    SpeedControllerGroup leftGroup = new SpeedControllerGroup(leftMotor);
      % endif
    % endif

    % if rightMotorPorts: # setup right side (if it exists)
    ${rightControllerTypes[0]} rightMotor = setup${rightControllerTypes[0]}(${rightMotorPorts[0]}, Sides.RIGHT, ${str(rightMotorsInverted[0]).lower()});
      % if controlType != "Simple":
        % for port in rightMotorPorts[1:]:
          % if controlType != "SparkMax":
    ${rightControllerTypes[loop.index + 1]} rightFollowerID${port} = setup${rightControllerTypes[loop.index + 1]}(${port}, Sides.FOLLOWER, ${str(rightMotorsInverted[loop.index + 1]).lower()});    
    rightFollowerID${port}.follow(rightMotor);
          % else:      
    CANSparkMax rightFollowerID${port} = setupCANSparkMax(${port}, Sides.FOLLOWER, ${str(rightMotorsInverted[loop.index + 1]).lower()});
    rightFollowerID${port}.follow(rightMotor, ${str(rightMotorsInverted[loop.index + 1]).lower()});
          % endif  
        % endfor
    drive = new DifferentialDrive(leftMotor, rightMotor);
      % else:
        % if len(rightMotorPorts) > 1:
    ArrayList<SpeedController> rightMotors = new ArrayList<SpeedController>();
          % for port in rightMotorPorts[1:]:
    rightMotors.add(setup${rightControllerTypes[loop.index + 1]}(${port}, Sides.FOLLOWER, ${str(rightMotorsInverted[loop.index + 1]).lower()}));
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
      % if controlType != "Simple":
    leaderMotor = leftMotor;
      % else:
    leaderMotor = leftGroup;
      % endif
    % endif

    //
    // Configure gyro
    //

    // Note that the angle from the NavX and all implementors of WPILib Gyro
    // must be negated because getAngle returns a clockwise positive angle
    % if gyroType == "ADXRS450":
    Gyro gyro = new ADXRS450_Gyro(${gyroPort});
    gyroAngleRadians = () -> -1 * Math.toRadians(gyro.getAngle());
    % elif gyroType == "AnalogGyro":
    Gyro gyro = new AnalogGyro(${gyroPort});
    gyroAngleRadians = () -> -1 * Math.toRadians(gyro.getAngle());
    % elif gyroType == "NavX":
    AHRS navx = new AHRS(${gyroPort});
    gyroAngleRadians = () -> -1 * Math.toRadians(navx.getAngle());
    % elif gyroType == "Pigeon":
    // Uncomment for Pigeon
    PigeonIMU pigeon = new PigeonIMU(${gyroPort});
    gyroAngleRadians = () -> {
      // Allocating a new array every loop is bad but concise
      double[] xyz = new double[3];
      pigeon.getAccumGyro(xyz);
      return Math.toRadians(xyz[2]);
    };
    % else:
    gyroAngleRadians = () -> 0.0;
    % endif

    // Set the update rate instead of using flush because of a ntcore bug
    // -> probably don't want to do this on a robot in competition
    NetworkTableInstance.getDefault().setUpdateRate(0.010);
  }

  @Override
  public void disabledInit() {
    double elapsedTime = Timer.getFPGATimestamp() - startTime;
    System.out.println("Robot disabled");
    % if rightMotorPorts:
    drive.tankDrive(0, 0);
    % else:
    leaderMotor.set(0);
    % endif
    // data processing step
    data = entries.toString();
    data = data.substring(1, data.length() - 1) + ", ";
    telemetryEntry.setString(data);
    entries.clear();
    System.out.println("Robot disabled");
    System.out.println("Collected : " + counter + " in " + elapsedTime + " seconds");
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
    % if rightMotorPorts:
    drive.arcadeDrive(-stick.getY(), stick.getX());
    % else:
    leaderMotor.set(-stick.getY());
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
    % if rightMotorPorts:
    drive.tankDrive(
      (rotateEntry.getBoolean(false) ? -1 : 1) * autospeed, autospeed,
      false
    );
    % else:
    leaderMotor.set(autospeed);
    % endif

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
    for (double num : numberArray) {
      entries.add(num);
    }
    counter++;
  }
}
