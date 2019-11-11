{
    # Ports for the motors
    "motorPorts": [0],
    # NOTE: Inversions of the slaves (i.e. any motor *after* the first on
    # each side of the drive) are *with respect to their master*.  This is
    # different from the other poject types!
    # Inversions for the motors
    "motorsInverted": [False],
    # Unit of analysis
    # Options:
    # 'Degrees'
    # 'Radians'
    # 'Rotations'
    "units": "Degrees",
    # The total gear reduction between the motor and the wheels, expressed as
    # a fraction [motor turns]/[wheel turns]
    "gearing": 1,
    # Encoder pulses-per-revolution (*NOT* cycles per revolution!)
    "encoderPPR": 512,
    # Whether the encoder is inverted
    "encoderInverted": False,
    # Offset of your encoder zero from horizontal
    "offset": 0,
}
