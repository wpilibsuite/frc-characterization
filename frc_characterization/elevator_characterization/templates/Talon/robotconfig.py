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
    # Pulley diameter (in units of your choice - will dictate units of analysis)
    "pulleyDiameter": 0.333,
    # This value should be the pulses per revolution *of the wheels*, and so
    # should take into account gearing between the encoder and the wheels
    "encoderPPR": 512,
    # Whether the encoder is inverted
    "encoderInverted": False,
}
