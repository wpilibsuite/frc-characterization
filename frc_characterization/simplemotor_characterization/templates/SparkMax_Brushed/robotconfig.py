{
    # Unit of analysis
    # Options:
    # 'Degrees'
    # 'Radians'
    # 'Rotations'
    "units": "Rotations",
    # Ports for the flywheel motor(s)
    # If you only have 1 motor all the below arrays should only have one element
    # The first port is the one with the encoder attached
    "motorPorts": [0, 1],
    # Note: Inversions of the slaves (i.e. any motor *after* the first) are
    # *with respect to their master*. This is different from the other poject types!
    # Inversions for the flywheel motor(s)
    "motorsInverted": [False, False],
    # Encoder edges-per-revolution (*NOT* cycles per revolution!)
    # This value should be the edges per revolution *of the wheels*, and so
    # should take into account gearing between the encoder and the wheels
    "encoderEPR": 512,
    # Whether the encoder is inverted
    "encoderInverted": False,
    # The total gear reduction between the motor and the flywheel, expressed as
    # a fraction [motor turns]/[wheel turns]
    "gearing": 1,
}
