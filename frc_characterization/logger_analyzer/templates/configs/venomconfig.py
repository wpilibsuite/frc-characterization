{
    # CAN device IDs for motors
    # If doing drive test, treat this as the left side of the drivetrain
    "motorPorts": [],
    # Only if you are doing drive (leave empty "[]" if not)
    "rightMotorPorts": [],
    # Class names of motor controllers used.
    # Options:
    # 'CANVenom'
    # If doing drive test, treat this as the left side of the drivetrain
    "controllerTypes": [],
    # Only if you are doing drive (leave empty "[]" if not)
    "rightControllerTypes": [],
    # Set motors to inverted or not
    # If doing drive test, treat this as the left side of the drivetrain
    "motorsInverted": [],
    # Only if you are doing drive (leave empty "[]" if not)
    "rightMotorsInverted": [],
    # Encoder edges-per-revolution (*NOT* cycles per revolution!)
    # encoderEPR is ignored when using the built in Venom encoder
    "encoderEPR": 1,
    # Gearing accounts for the gearing between the encoder and the output shaft
    "gearing": 1,
    # Encoder ports
    # If doing drive test, treat this as the left side of the drivetrain
    # Leave empty "[]" if using the built in Venom encoder
    "encoderPorts": [],
    # Only if you are doing drive (leave empty "[]" if not)
    "rightEncoderPorts": [],
    # Set to True if encoders need to be inverted
    # If doing drive test, treat this as the left side of the drivetrain
    "encoderInverted": False,
    # Only if you are doing drive (set to False if not needed)
    "rightEncoderInverted": False,
    # ** The following is only if you are using a gyro for the DriveTrain test**
    # Gyro type (one of "NavX", "Pigeon", "ADXRS450", "AnalogGyro", or "None")
    "gyroType": "None",
    # Whatever you put into the constructor of your gyro
    # Could be:
    # "SPI.Port.kMXP" (MXP SPI port for NavX or ADXRS450),
    # "SerialPort.Port.kMXP" (MXP Serial port for NavX),
    # "I2C.Port.kOnboard" (Onboard I2C port for NavX),
    # "0" (Pigeon CAN ID or AnalogGyro channel),
    # "new WPI_TalonSRX(3)" (Pigeon on a Talon SRX),
    # "" (NavX using default SPI, ADXRS450 using onboard CS0, or no gyro)
    "gyroPort": "",
}
