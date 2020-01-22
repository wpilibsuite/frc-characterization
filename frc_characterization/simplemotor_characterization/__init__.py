from mako.template import Template

import os
import importlib.resources as resources


def genRobotCode(projectType, config):
    if projectType == "Simple":
        with resources.path(__name__, "templates") as path:
            with open(os.path.join(path, "Simple", "Robot.java.mako"), "r") as template:
                return Template(template.read()).render(
                    epr=config["encoderEPR"],
                    units=config["units"],
                    ports=config["motorPorts"],
                    inverted=config["motorsInverted"],
                    controllers=config["controllerTypes"],
                    encoderports=config["encoderPorts"],
                    encoderinv=config["encoderInverted"],
                )
    elif projectType == "Talon":
        with resources.path(__name__, "templates") as path:
            with open(os.path.join(path, "Talon", "Robot.java.mako"), "r") as template:
                return Template(template.read()).render(
                    epr=config["encoderEPR"],
                    units=config["units"],
                    ports=config["motorPorts"],
                    inverted=config["motorsInverted"],
                    controllers=config["controllerTypes"],
                    encoderinv=config["encoderInverted"],
                )
    elif projectType == "SparkMax_Brushed":
        with resources.path(__name__, "templates") as path:
            with open(
                os.path.join(path, "SparkMax_Brushed", "Robot.java.mako"), "r"
            ) as template:
                return Template(template.read()).render(
                    epr=config["encoderEPR"],
                    units=config["units"],
                    gearing=config["gearing"],
                    ports=config["motorPorts"],
                    inverted=config["motorsInverted"],
                    encoderinv=config["encoderInverted"],
                )
    elif projectType == "SparkMax_Brushless":
        with resources.path(__name__, "templates") as path:
            with open(
                os.path.join(path, "SparkMax_Brushless", "Robot.java.mako"), "r"
            ) as template:
                return Template(template.read()).render(
                    units=config["units"],
                    gearing=config["gearing"],
                    ports=config["motorPorts"],
                    inverted=config["motorsInverted"],
                )


def genBuildGradle(projectType, team):
    with resources.path(__name__, "templates") as path:
        with open(
            os.path.join(path, projectType, "build.gradle.mako"), "r"
        ) as template:
            return Template(template.read()).render(team=team)
