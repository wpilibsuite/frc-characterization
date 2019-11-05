{
    # Class names of motor controllers used.
    # Options:
    # 'WPI_TalonSRX'
    # 'WPI_VictorSPX'
    # Note: The first motor should always be a TalonSRX, as the VictorSPX
    # does not support encoder connections.
    "controllerTypes": ["WPI_TalonSRX"],
    # Ports for the motors
    "motorPorts": [0],
    # Inversions for the motors
    "motorsInverted": [False],
    # Unit of analysis
    # Options:
    # 'Degrees'
    # 'Radians'
    # 'Rotations'
    "units": "Degrees",
    # Encoder pulses-per-revolution (*NOT* cycles per revolution!)
    # This value should be the pulses per revolution *of the arm*, and so
    # should take into account gearing between the encoder and the arm
    "encoderPPR": 512,
    # Whether the encoder is inverted
    "encoderInverted": False,
    # Offset of your encoder zero from horizontal
    "offset": 0,
}
