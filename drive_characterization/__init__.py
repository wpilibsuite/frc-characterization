from mako.template import Template

import os
import importlib.resources as resources


def genRobotCode(projectType, config):
    if projectType == 'Simple':
        with resources.path(__name__, 'templates') as path:
            with open(os.path.join(path, 'Simple', 'Robot.mako'), 'r') as template:
                return Template(template.read()).render(
                    diam=config['wheelDiameter'],
                    ppr=config['encoderPPR'],
                    lports=config['leftMotorPorts'],
                    rports=config['rightMotorPorts'],
                    linverted=config['leftMotorsInverted'],
                    rinverted=config['rightMotorsInverted'],
                    lcontrollers=config['leftControllerTypes'],
                    rcontrollers=config['rightControllerTypes'],
                    turn=config['turn'],
                    lencoderports=config['leftEncoderPorts'],
                    rencoderports=config['rightEncoderPorts'],
            )
    elif projectType == 'Talon':
        print('not yet supported :<')

