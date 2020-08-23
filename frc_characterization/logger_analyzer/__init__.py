from mako.template import Template

import os
import importlib.resources as resources


def gen_robot_code(config):
    with resources.path(__name__, "templates") as path:
        with open(os.path.join(path, "Robot.java.mako"), "r") as template:
            return Template(template.read()).render(**config)


def gen_build_gradle(team):
    with resources.path(__name__, "templates") as path:
        with open(os.path.join(path, "build.gradle.mako"), "r") as template:
            return Template(template.read()).render(team=team)
