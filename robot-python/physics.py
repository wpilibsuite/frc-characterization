#
# See the notes for the other physics sample
#


import math
from pyfrc.physics import motor_cfgs, tankmodel
from pyfrc.physics.units import units


class PhysicsEngine(object):
    '''
       Simulates a 4-wheel robot using Tank Drive joystick control
    '''
    
    WHEEL_DIAMETER = 6*units.inch
    ENCODER_PULSE_PER_REV = 360
    
    ENCODER_SCALE = (units.foot.m_from(WHEEL_DIAMETER) * math.pi / 360)
    
    def __init__(self, physics_controller):
        '''
            :param physics_controller: `pyfrc.physics.core.Physics` object
                                       to communicate simulation effects to
        '''
        
        self.physics_controller = physics_controller
        
        #
        # Two ways of initializing the realistic physics -- either use the
        # ka/kv that you computed for your robot, or use the theoretical model
        #
        
        # Change these parameters to fit your robot!
        # -> these parameters are for the test robot mentioned in the paper
        motor_cfg = motor_cfgs.MOTOR_CFG_CIM
        robot_mass = 110*units.lbs
        
        bumper_width = 3.25*units.inch
        robot_wheelbase = 22*units.inch
        robot_width = 23*units.inch + bumper_width*2
        robot_length = 32*units.inch + bumper_width*2
        
        wheel_diameter = 3.8*units.inch
        drivetrain_gear_ratio = 6.1
        motors_per_side = 3
        
        # Uses theoretical parameters by default, change this if you've
        # actually measured kv/ka for your robot
        if True:
        
            self.drivetrain = tankmodel.TankModel.theory(motor_cfg,
                                                         robot_mass, drivetrain_gear_ratio, motors_per_side,
                                                         robot_wheelbase,
                                                         robot_width,
                                                         robot_length,
                                                         wheel_diameter)
        else:
            # These are the parameters for kv/ka that you computed for your robot
            # -> this example uses the values from the paper
            l_kv = 0.81*units.tm_kv
            l_ka = 0.21*units.tm_ka
            l_vintercept = 1.26*units.volts
            r_kv = 0.81*units.tm_kv
            r_ka = 0.21*units.tm_ka
            r_vintercept = 1.26*units.volts
            
            self.drivetrain = tankmodel.TankModel(motor_cfg,
                                                  robot_mass,
                                                  robot_wheelbase,
                                                  robot_width,
                                                  robot_length,
                                                  l_kv, l_ka, l_vintercept,
                                                  r_kv, r_ka, r_vintercept)
            

    def update_sim(self, hal_data, now, tm_diff):
        '''
            Called when the simulation parameters for the program need to be
            updated.
            
            :param now: The current time as a float
            :param tm_diff: The amount of time that has passed since the last
                            time that this function was called
        '''
        
        # TODO: simulate battery voltage effects
        hal_data['power']['vin_voltage'] = 12.0
        
        # Simulate the drivetrain
        lr_motor = hal_data['pwm'][1]['value'] * -1
        rr_motor = hal_data['pwm'][2]['value'] * -1
        
        # Not needed because front and rear should be in sync
        #lf_motor = hal_data['pwm'][3]['value']
        #rf_motor = hal_data['pwm'][4]['value']
        
        x, y, angle = self.drivetrain.get_distance(lr_motor, rr_motor, tm_diff)
        self.physics_controller.distance_drive(x, y, angle)
        
        # set the position / velocity on the encoder
        
        left_counter = self.drivetrain.l_position / self.ENCODER_SCALE
        right_counter = self.drivetrain.r_position / self.ENCODER_SCALE
        hal_data['encoder'][0]['count'] = int(left_counter)
        hal_data['encoder'][1]['count'] = int(right_counter)
        
        # bug: HAL 2018 rate isn't scaled correctly, so put the actual velocity in
        left_velocity = self.drivetrain.l_velocity # / self.ENCODER_SCALE
        right_velocity = self.drivetrain.r_velocity # / self.ENCODER_SCALE
        hal_data['encoder'][0]['rate'] = left_velocity
        hal_data['encoder'][1]['rate'] = right_velocity
        
