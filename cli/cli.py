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


def armDataLogger(dir):
    arm_characterization.data_logger.main()


def armDataAnalyzer(dir):
    arm_characterization.data_analyzer.main()


def armNewProject(dir):
    print(dir)


def driveDataLogger(dir):
    drive_characterization.data_logger.main()


def driveDataAnalyzer(dir):
    drive_characterization.data_analyzer.main()


def driveNewProject(dir):

    if not dir:
        dir = filedialog.askdirectory(title = "Choose directory for characterization robot project",
                                       initialdir = getcwd())

    dir = os.path.join(dir, "characterization_project")

    with resources.path(drive_characterization, "robot") as path:
        shutil.copytree(src=path, dst=dir)

    # shutil.copytree(src=resources.path(robot), dst=dir)

def elevatorDataLogger(dir):
    elevator_characterization.data_logger.main()


def elevatorDataAnalyzer(dir):
    elevator_characterization.data_analyzer.main()


def elevatorNewProject(dir):
    print(dir)


# def elevatorDataLogger():
#     from elevator_characterization.data_logger import main
#     main()

# def elevatorDataAnalyzer():
#     from elevator_characterization.data_analyzer import main
#     main()

tool_dict = {
    "drive": {
        "new": driveNewProject,
        "logger": driveDataLogger,
        "analyzer": driveDataAnalyzer,
    },
    "arm": {
        "new": armNewProject,
       "logger": armDataLogger,
        "analyzer": armDataAnalyzer,
    },
    "elevator": {
        "new": elevatorNewProject,
        "logger": elevatorDataLogger,
        "analyzer": elevatorDataAnalyzer,
    }
}


def main():

    if len(argv) < 2:
        menu = SelectionMenu(list(tool_dict.keys()), "What type of mechanism are you characterizing?")
        menu.show()
        menu.join()
        mech_type = list(tool_dict.keys())[menu.selected_option]

        menu = SelectionMenu(list(list(tool_dict.values())[0].keys()), "What tool do you want to use?")
        menu.show()
        menu.join()
        tool_type = list(list(tool_dict.values())[0].keys())[menu.selected_option]

        tool_dict[mech_type][tool_type](None)
    else:
        parser = argparse.ArgumentParser(description="RobotPy characterization tools CLI")
        parser.add_argument(
            "mech_type",
            choices=list(tool_dict.keys()), 
            help="Mechanism type being characterized"
        )
        parser.add_argument(
            "tool_type", 
            choices=list(list(tool_dict.values())[0].keys()),
            help="Tool type to use"
        )
        parser.add_argument(
            "project_directory",
            help="The project directory if creating a new project",
            nargs = "?",
            default = None
        )
        argcomplete.autocomplete(parser)

        args = parser.parse_args()
        tool_dict[args.mech_type][args.tool_type](args.project_directory)


if __name__ == "__main__":

    main()
