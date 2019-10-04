from mako.template import Template

import os
import importlib.resources as resources


def genRobotCode(projectType, config):
    if projectType == 'Simple':
        with resources.path(__name__, 'templates') as path:
            with open(os.path.join(path, 'Simple', 'Robot.java.mako'), 'r') as template:
                return Template(template.read()).render(
                    diam=config['pulleyDiameter'],
                    ppr=config['encoderPPR'],
                    ports=config['motorPorts'],
                    inverted=config['motorsInverted'],
                    controllers=config['controllerTypes'],
                    encoderports=config['encoderPorts'],
                    encoderinv=config['encoderInverted'],
            )
    elif projectType == 'Talon':
        with resources.path(__name__, 'templates') as path:
            with open(os.path.join(path, 'Talon', 'Robot.java.mako'), 'r') as template:
                return Template(template.read()).render(
                    diam=config['pulleyDiameter'],
                    ppr=config['encoderPPR'],
                    ports=config['motorPorts'],
                    inverted=config['motorsInverted'],
                    controllers=config['controllerTypes'],
                    encoderinv=config['encoderInverted'],
            )

def genBuildGradle(projectType, team):
    with resources.path(__name__, 'templates') as path:
        with open(os.path.join(path, projectType, 'build.gradle.mako'), 'r') as template:
            return Template(template.read()).render(team=team)