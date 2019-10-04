{
  # Class names of motor controllers used.
  # Options:
  # 'Spark'
  # 'Victor'
  # 'VictorSP'
  # 'PWMTalonSRX'
  # 'PWMVictorSPX'
  # 'WPI_TalonSRX'
  # 'WPI_VictorSPX'
  'controllerTypes': ('Spark',),
  
  # Ports for the motors
  'motorPorts': (0,),

  # Inversions for the motors
  'motorsInverted': (False,),

  # Pulley diameter (in units of your choice - will dictate units of analysis)
  'pulleyDiameter': .333,

  # This value should be the pulses per revolution *of the pulley*, and so
  # should take into account gearing between the encoder and the pulley
  'encoderPPR': 512,
  # Ports for the left-side encoder
  'encoderPorts': (0, 1),
  # Whether the left encoder is inverted
  'encoderInverted': False,
}
