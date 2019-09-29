import drive_characterization.data_analyzer
import drive_characterization.data_logger
import arm_characterization.data_analyzer
import arm_characterization.data_logger
import elevator_characterization.data_analyzer
import elevator_characterization.data_logger

import argparse
import argcomplete
from consolemenu import SelectionMenu
from tkinter import filedialog

import os
from os import getcwd
from sys import argv
import shutil

# import pkg_resources
import importlib.resources as resources

langs = ("java", "cpp", "python")

controllers = ("spark", "talonsrx")


def newProject(dir, mech):

    if not dir:
        dir = filedialog.askdirectory(
            title="Choose directory for characterization robot project",
            initialdir=getcwd(),
        )

    dir = os.path.join(dir, "characterization_project")

    menu = SelectionMenu(langs, "Select programming language")
    menu.show()
    menu.join()
    lang = langs[menu.selected_option]

    menu = SelectionMenu(controllers, "Select your motor controller model")
    menu.show()
    menu.join()
    controller = controllers[menu.selected_option]

    proj = "robot-" + lang + "-" + controller

    with resources.path(mech, "robot") as path:
        path = os.path.join(path, proj)
        shutil.copytree(src=path, dst=dir)


def loggerArm(dir):
    arm_characterization.data_logger.main()


def analyzerArm(dir):
    arm_characterization.data_analyzer.main()


def loggerDrive(dir):
    drive_characterization.data_logger.main()


def analyzerDrive(dir):
    drive_characterization.data_analyzer.main()


def loggerElevator(dir):
    elevator_characterization.data_logger.main()


def analyzerElevator(dir):
    elevator_characterization.data_analyzer.main()


# def elevatorDataLogger():
#     from elevator_characterization.data_logger import main
#     main()

# def elevatorDataAnalyzer():
#     from elevator_characterization.data_analyzer import main
#     main()

tool_dict = {
    "drive": {
        "new": lambda dir: newProject(dir, drive_characterization),
        "logger": loggerDrive,
        "analyzer": analyzerDrive,
    },
    "arm": {
        "new": lambda dir: newProject(dir, arm_characterization),
        "logger": loggerArm,
        "analyzer": analyzerArm,
    },
    "elevator": {
        "new": lambda dir: newProject(dir, elevator_characterization),
        "logger": loggerElevator,
        "analyzer": analyzerElevator,
    },
}


def main():

    if len(argv) < 2:
        menu = SelectionMenu(
            list(tool_dict.keys()), "What type of mechanism are you characterizing?"
        )
        menu.show()
        menu.join()
        mech_type = list(tool_dict.keys())[menu.selected_option]

        menu = SelectionMenu(
            list(list(tool_dict.values())[0].keys()), "What tool do you want to use?"
        )
        menu.show()
        menu.join()
        tool_type = list(list(tool_dict.values())[0].keys())[menu.selected_option]

        tool_dict[mech_type][tool_type](None)
    else:
        parser = argparse.ArgumentParser(
            description="RobotPy characterization tools CLI"
        )
        parser.add_argument(
            "mech_type",
            choices=list(tool_dict.keys()),
            help="Mechanism type being characterized",
        )
        parser.add_argument(
            "tool_type",
            choices=list(list(tool_dict.values())[0].keys()),
            help="Tool type to use",
        )
        parser.add_argument(
            "project_directory",
            help="The project directory if creating a new project",
            nargs="?",
            default=None,
        )
        argcomplete.autocomplete(parser)

        args = parser.parse_args()
        tool_dict[args.mech_type][args.tool_type](args.project_directory)


if __name__ == "__main__":

    main()
