{
  # Class names of motor controllers used.
  # Options:
  # 'Spark'
  # 'Victor'
  # 'Victor SP'
  # 'PWMTalonSRX'
  # 'PWMVictorSPX'
  'rightControllerTypes': ('Spark', 'Spark'),
  'leftControllerTypes': ('Spark', 'Spark'),

  # Wheel diameter (in units of your choice - will dictate units of analysis)
  'wheelDiameter': .333,

  # Encoder pulses-per-revolution (*NOT* cycles per revolution!)
  'encoderPPR': 512,
  # Ports for the left-side encoder
  'leftEncoderPorts': (0, 1),
  # Ports for the right-side encoder
  'rightEncoderPorts': (2, 3),

  # Ports for the left-side motors
  'leftMotorPorts': (0, 1),
  # Ports for the right-side motors
  'rightMotorPorts': (2, 3),

  # Inversions for the left-side motors
  'leftMotorsInverted': (False, False),
  # Inversions for the right side motors
  'rightMotorsInverted': (False, False),

  # Whether the robot should turn (for angular tests)
  'turn': False,
}
