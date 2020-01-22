{
    # Unit of analysis
    # Options:
    # 'Degrees'
    # 'Radians'
    # 'Rotations'
    "units": "Rotations",
    # Ports for the flywheel motors
    # If you only have 1 motor all the below arrays should only have one element
    # The first port is the port for the motor whose encoder will be used
    "motorPorts": [0, 1],
    # Note: Inversions of the slaves (i.e. any motor *after* the first) are
    # *with respect to their master*. This is different from the other poject types!
    # Inversions for the flywheel motor(s)
    "motorsInverted": [False, False],
    # The total gear reduction between the motor and the wheels, expressed as
    # a fraction [motor turns]/[wheel turns]
    "gearing": 1,
}
