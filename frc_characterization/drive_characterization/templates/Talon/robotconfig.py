{
  # Class names of motor controllers used.
  # Options:
  # 'WPI_TalonSRX'
  # 'WPI_VictorSPX'
  # Note: The first motor on each side should always be a TalonSRX, as the
  # VictorSPX does not support encoder connections
  'rightControllerTypes': ('WPI_TalonSRX', 'WPI_TalonSRX'),
  'leftControllerTypes': ('WPI_TalonSRX', 'WPI_TalonSRX'),

  # Ports for the left-side motors
  'leftMotorPorts': (0, 1),
  # Ports for the right-side motors
  'rightMotorPorts': (2, 3),

  # Inversions for the left-side motors
  'leftMotorsInverted': (False, False),
  # Inversions for the right side motors
  'rightMotorsInverted': (False, False),

  # Wheel diameter (in units of your choice - will dictate units of analysis)
  'wheelDiameter': .333,

  # If your robot has only one encoder, remove all of the right encoder fields
  # Encoder pulses-per-revolution (*NOT* cycles per revolution!)
  # This value should be the pulses per revolution *of the wheels*, and so
  # should take into account gearing between the encoder and the wheels
  'encoderPPR': 512,
  # Whether the left encoder is inverted
  'leftEncoderInverted': False,
  # Whether the right encoder is inverted:
  'rightEncoderInverted': False,

  # Whether the robot should turn (for angular tests)
  'turn': False,
}
