{
    # Unit of analysis
    # Options:
    # 'Degrees'
    # 'Radians'
    # 'Rotations'
    "units": "Rotations",
    # Class names of motor controllers used.
    # Options:
    # 'Spark'
    # 'Victor'
    # 'VictorSP'
    # 'PWMTalonSRX'
    # 'PWMVictorSPX'
    # 'WPI_TalonSRX'
    # 'WPI_VictorSPX'
    # If you only have 1 motor all the below arrays should only have one element
    "controllerTypes": ["Spark", "Spark"],
    # Ports for the flywheel motor(s)
    # The first port is the one with the encoder attached
    "motorPorts": [0, 1],
    # Inversions for the left-flywheel motor(s)
    "motorsInverted": [False, False],
    # Encoder edges-per-revolution (*NOT* cycles per revolution!)
    # This value should be the edges per revolution *of the flywheel*, and so
    # should take into account gearing between the encoder and the wheels
    "encoderEPR": 512,
    # Ports for the flywheel encoder
    "encoderPorts": [0, 1],
    # Whether the encoder is inverted
    "encoderInverted": False,
}
