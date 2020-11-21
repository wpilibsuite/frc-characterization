{
    # Set to True if the spark max will be brushed
    # ** WARNING: Improperly setting this can break things **
    "brushed": False,
    # Ports for motors
    # If doing drive test, treat this as the left side of the drivetrain
    "motorPorts": [],
    # Only if you are doing drive (leave empty "[]" if not)
    "rightMotorPorts": [],
    # Set motors to inverted or not
    # If doing drive test, treat this as the left side of the drivetrain
    "motorsInverted": [],
    # Only if you are doing drive (leave empty "[]" if not)
    "rightMotorsInverted": [],
    # Encoder edges-per-revolution (*NOT* cycles per revolution!)
    # **Note pass an EPR of 1 for the NEO Integrated encoder as the SparkMax
    # already handles this conversion**
    # For the REV Through Bore Encoder, use 8192 (2048 * 4)
    "encoderEPR": 1,
    # Gearing accounts for the gearing between the encoder and the output shaft
    "gearing": 1,
    # Set this to True if you would like to use the SparkMax Data Port
    # Note that the Data Port is the 10 pin port on the top of the SparkMax
    # Setting this to False indicates you want to use the 6 pin encoder port
    # which is located in the front of the SparkMax
    "useDataPort": True,
    # Encoder ports (leave empty "[]" if not needed)
    # Specifying encoder ports indicates you want to use Rio-side encoders
    # If doing drive test, treat this as the left side of the drivetrain
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
