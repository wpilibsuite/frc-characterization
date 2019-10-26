# The CLI entry point for the characterization toolsuite.

import argparse
import importlib.resources as resources
import os
import shutil
from os import getcwd
from sys import argv
from tkinter import filedialog

import argcomplete
import arm_characterization.data_analyzer
import arm_characterization.data_logger
import drive_characterization.data_analyzer
import drive_characterization.data_logger
import elevator_characterization.data_analyzer
import elevator_characterization.data_logger
import logger_gui
import newproject
from consolemenu import SelectionMenu

langs = ("java", "cpp", "python")

controllers = ("spark", "talonsrx")


def newProject(dir, mech):
    newproject.main(mech)


def loggerArm(dir):
    logger_gui.main(0, getcwd(), arm_characterization.data_logger.TestRunner)


def analyzerArm(dir):
    arm_characterization.data_analyzer.main(getcwd())


def loggerDrive(dir):
    logger_gui.main(0, getcwd(), drive_characterization.data_logger.TestRunner)


def analyzerDrive(dir):
    drive_characterization.data_analyzer.main(getcwd())


def loggerElevator(dir):
    logger_gui.main(0, getcwd(), elevator_characterization.data_logger.TestRunner)


def analyzerElevator(dir):
    elevator_characterization.data_analyzer.main(getcwd())


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
            description="FRC characterization tools CLI"
        )
        parser.add_argument(
            "mech_type",
            choices=list(tool_dict.keys()),
            help="Mechanism type being characterized",
        )
        parser.add_argument(
            "tool_type",
            choices=list(list(tool_dict.values())[0].keys()),
            help="Create new project, start data recorder/logger, or start data analyzer",
        )
        parser.add_argument(
            "project_directory",
            help="Location for the project directory (if creating a new project)",
            nargs="?",
            default=None,
        )
        argcomplete.autocomplete(parser)

        args = parser.parse_args()
        tool_dict[args.mech_type][args.tool_type](args.project_directory)


if __name__ == "__main__":

    main()
