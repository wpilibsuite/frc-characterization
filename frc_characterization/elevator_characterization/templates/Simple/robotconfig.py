{
    # Class names of motor controllers used.
    # Options:
    # 'WPI_TalonSRX'
    # 'WPI_VictorSPX'
    # Note: The first motor should always be a TalonSRX, as the VictorSPX
    # does not support encoder connections.
    "controllerTypes": ["Spark"],
    # Ports for the motors
    "motorPorts": [0],
    # Inversions for the motors
    "motorsInverted": [False],
    # Pulley diameter (in units of your choice - will dictate units of analysis)
    "pulleyDiameter": 0.333,
    # This value should be the pulses per revolution *of the pulley*, and so
    # should take into account gearing between the encoder and the pulley
    "encoderPPR": 512,
    # Ports for the encoder
    "encoderPorts": [0, 1],
    # Whether the encoder is inverted
    "encoderInverted": False,
}
