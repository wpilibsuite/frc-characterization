from mako.template import Template

import os
import importlib.resources as resources


def genRobotCode(projectType, config):
    if projectType == "Simple":
        with resources.path(__name__, "templates") as path:
            with open(os.path.join(path, "Simple", "Robot.java.mako"), "r") as template:
                return Template(template.read()).render(
                    diam=config["wheelDiameter"],
                    epr=config["encoderEPR"],
                    lports=config["leftMotorPorts"],
                    rports=config["rightMotorPorts"],
                    linverted=config["leftMotorsInverted"],
                    rinverted=config["rightMotorsInverted"],
                    lcontrollers=config["leftControllerTypes"],
                    rcontrollers=config["rightControllerTypes"],
                    lencoderports=config["leftEncoderPorts"],
                    rencoderports=config["rightEncoderPorts"],
                    lencoderinv=config["leftEncoderInverted"],
                    rencoderinv=config["rightEncoderInverted"],
                    gyro=config["gyroType"],
                    gyroport=config["gyroPort"],
                )
    elif projectType == "Talon":
        with resources.path(__name__, "templates") as path:
            with open(os.path.join(path, "Talon", "Robot.java.mako"), "r") as template:
                return Template(template.read()).render(
                    diam=config["wheelDiameter"],
                    epr=config["encoderEPR"],
                    lports=config["leftMotorPorts"],
                    rports=config["rightMotorPorts"],
                    linverted=config["leftMotorsInverted"],
                    rinverted=config["rightMotorsInverted"],
                    lcontrollers=config["leftControllerTypes"],
                    rcontrollers=config["rightControllerTypes"],
                    lencoderinv=config["leftEncoderInverted"],
                    rencoderinv=config["rightEncoderInverted"],
                    gyro=config["gyroType"],
                    gyroport=config["gyroPort"],
                )
    elif projectType == "SparkMax_Brushed":
        with resources.path(__name__, "templates") as path:
            with open(
                os.path.join(path, "SparkMax_Brushed", "Robot.java.mako"), "r"
            ) as template:
                return Template(template.read()).render(
                    diam=config["wheelDiameter"],
                    epr=config["encoderEPR"],
                    gearing=config["gearing"],
                    lports=config["leftMotorPorts"],
                    rports=config["rightMotorPorts"],
                    linverted=config["leftMotorsInverted"],
                    rinverted=config["rightMotorsInverted"],
                    lencoderinv=config["leftEncoderInverted"],
                    rencoderinv=config["rightEncoderInverted"],
                    gyro=config["gyroType"],
                    gyroport=config["gyroPort"],
                )
    elif projectType == "SparkMax_Brushless":
        with resources.path(__name__, "templates") as path:
            with open(
                os.path.join(path, "SparkMax_Brushless", "Robot.java.mako"), "r"
            ) as template:
                return Template(template.read()).render(
                    diam=config["wheelDiameter"],
                    gearing=config["gearing"],
                    lports=config["leftMotorPorts"],
                    rports=config["rightMotorPorts"],
                    linverted=config["leftMotorsInverted"],
                    rinverted=config["rightMotorsInverted"],
                    gyro=config["gyroType"],
                    gyroport=config["gyroPort"],
                )


def genBuildGradle(projectType, team):
    with resources.path(__name__, "templates") as path:
        with open(
            os.path.join(path, projectType, "build.gradle.mako"), "r"
        ) as template:
            return Template(template.read()).render(team=team)
