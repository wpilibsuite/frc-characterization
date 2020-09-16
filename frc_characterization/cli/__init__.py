# The CLI entry point for the characterization toolsuite.

import argparse
from os import getcwd
from sys import argv
from functools import partial

import argcomplete
import frc_characterization
import frc_characterization.arm_characterization.data_analyzer as arm_analyzer
import frc_characterization.arm_characterization.data_logger as arm_logger
import frc_characterization.drive_characterization.data_analyzer as drive_analyzer
import frc_characterization.drive_characterization.data_logger as drive_logger
import frc_characterization.elevator_characterization.data_analyzer as elevator_analyzer
import frc_characterization.elevator_characterization.data_logger as elevator_logger
import frc_characterization.simplemotor_characterization.data_analyzer as simplemotor_analyzer
import frc_characterization.simplemotor_characterization.data_logger as simplemotor_logger
import frc_characterization.logger_gui as logger_gui
import frc_characterization.newproject as newproject

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem

langs = ("java", "cpp", "python")

controllers = ("spark", "talonsrx")


def newProject(mechanism, directory=None):
    newproject.main(mechanism)


def loggerArm(directory=None):
    logger_gui.main(0, getcwd(), arm_logger.TestRunner)


def analyzerArm(directory=None):
    arm_analyzer.main(getcwd())


def loggerDrive(directory=None):
    logger_gui.main(0, getcwd(), drive_logger.TestRunner)


def analyzerDrive(directory=None):
    drive_analyzer.main(getcwd())


def loggerElevator(directory=None):
    logger_gui.main(0, getcwd(), elevator_logger.TestRunner)


def analyzerElevator(directory=None):
    elevator_analyzer.main(getcwd())


def loggerSimpleMotor(directory=None):
    logger_gui.main(0, getcwd(), simplemotor_logger.TestRunner)


def analyzerSimpleMotor(directory=None):
    simplemotor_analyzer.main(getcwd())


tool_dict = {
    "drive": {
        "new": partial(
            newProject,
            mechanism=frc_characterization.drive_characterization,
        ),
        "logger": loggerDrive,
        "analyzer": analyzerDrive,
    },
    "arm": {
        "new": partial(newProject, mechanism=frc_characterization.arm_characterization),
        "logger": loggerArm,
        "analyzer": analyzerArm,
    },
    "elevator": {
        "new": partial(
            newProject,
            mechanism=frc_characterization.elevator_characterization,
        ),
        "logger": loggerElevator,
        "analyzer": analyzerElevator,
    },
    "simple-motor": {
        "new": partial(
            newProject,
            mechanism=frc_characterization.simplemotor_characterization,
        ),
        "logger": loggerSimpleMotor,
        "analyzer": analyzerSimpleMotor,
    },
}


def main():

    if len(argv) < 2:
        menu = ConsoleMenu(
            "Mechanism Types", "Choose which mechanism you are characterizing"
        )

        for mechanism, tools in tool_dict.items():
            tool_menu = ConsoleMenu(f"Characterization Tools: {mechanism}")
            for tool, function in tools.items():
                tool_menu.append_item(FunctionItem(tool, function, menu=tool_menu))

            menu.append_item(SubmenuItem(mechanism, tool_menu, menu))

        menu.show()

    else:
        parser = argparse.ArgumentParser(description="FRC characterization tools CLI")
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
        tool_dict[args.mech_type][args.tool_type](directory=args.project_directory)


if __name__ == "__main__":

    main()
