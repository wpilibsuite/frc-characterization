{
    # Ports for the motors
    "motorPorts": [0],
    # NOTE: Inversions of the slaves (i.e. any motor *after* the first on
    # each side of the drive) are *with respect to their master*.  This is
    # different from the other poject types!
    # Inversions for the motors
    "motorsInverted": [False],
    # The total gear reduction between the motor and the pulley, expressed as
    # a fraction [motor turns]/[pulley turns]
    "gearing": 1,
    # Pulley diameter (in units of your choice - will dictate units of analysis)
    "pulleyDiameter": 0.333,
    # Offset of your encoder zero from horizontal
    "offset": 0,
}
