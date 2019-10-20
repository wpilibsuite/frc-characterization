{
  # Ports for the left-side motors
  'leftMotorPorts': (0, 1),
  # Ports for the right-side motors
  'rightMotorPorts': (2, 3),

  # NOTE: Inversions of the slaves (i.e. any motor *after* the first on
  # each side of the drive) are *with respect to their master*.  This is
  # different from the other poject types!
  # Inversions for the left-side motors
  'leftMotorsInverted': (False, False),
  # Inversions for the right side motors
  'rightMotorsInverted': (False, False),

  # If your robot has only one encoder, remove all of the right encoder fields
  # Encoder pulses-per-revolution (*NOT* cycles per revolution!)
  # This value should be the pulses per revolution *of the wheels*, and so
  # should take into account gearing between the encoder and the wheels
  'encoderPPR': 512,
  # Whether the left encoder is inverted
  'leftEncoderInverted': False,
  # Whether the right encoder is inverted:
  'rightEncoderInverted': False,

  # The total gear reduction between the motor and the wheels, expressed as
  # a fraction [motor turns]/[wheel turns]
  'gearing': 1,
  # Wheel diameter (in units of your choice - will dictate units of analysis)
  'wheelDiameter': .333,

  # Whether the robot should turn (for angular tests)
  'turn': False,
}
