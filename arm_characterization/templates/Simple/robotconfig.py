{
  # Class names of motor controllers used.
  # Options:
  # 'Spark'
  # 'Victor'
  # 'Victor_SP'
  # 'PWMTalonSRX'
  # 'PWMVictorSPX'
  # 'WPI_TalonSRX'
  # 'WPI_VictorSPX'
  'controllerTypes': ('Spark'),
  
  # Ports for the motors
  'motorPorts': (0),

  # Inversions for the motors
  'motorsInverted': (False),

  # If your robot has only one encoder, remove all of the right encoder fields
  # Encoder pulses-per-revolution (*NOT* cycles per revolution!)
  # This value should be the pulses per revolution *of the wheels*, and so
  # should take into account gearing between the encoder and the wheels
  'encoderPPR': 512,
  # Ports for the left-side encoder
  'encoderPorts': (0, 1),
  # Whether the left encoder is inverted
  'encoderInverted': False,
}
