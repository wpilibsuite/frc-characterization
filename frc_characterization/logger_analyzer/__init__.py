from mako.template import Template

import os
import importlib.resources as resources


def genRobotCode(config):

    with resources.path(__name__, "templates") as path:
        with open(os.path.join(path, "Robot.java.mako"), "r") as template:
            return Template(template.read()).render(
                control=config[
                    "controlType"
                ],  # this replaces the different control types initially specified in the GUI
                # left controller values are generic to accomodate for tests that require only one set of motorcontrollers
                epr=config["encoderEPR"],
                ports=config["motorPorts"],
                inverted=config["motorsInverted"],
                controller=config["controllerTypes"],
                encoderinv=config["encoderInverted"],
                encoderports=config["encoderPorts"],
                # these will only be used if a drivetrain test is being conducted
                rightcontroller=config["rightControllerTypes"],
                rightinverted=config["rightMotorsInverted"],
                rightports=config["rightMotorPorts"],
                rencoderports=config["rightEncoderPorts"],
                rencoderinv=config["rightEncoderInverted"],
                gyro=config["gyroType"],
                gyroport=config["gyroPort"],
                gearing=config["gearing"],
                integrated=config["useIntegrated"],
            )


def genBuildGradle(team):
    with resources.path(__name__, "templates") as path:
        with open(os.path.join(path, "build.gradle.mako"), "r") as template:
            return Template(template.read()).render(team=team)
