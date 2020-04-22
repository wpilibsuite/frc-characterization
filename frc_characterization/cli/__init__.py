# The CLI entry point for the characterization toolsuite.

import argparse
from os import getcwd
from sys import argv
from functools import partial

import argcomplete
import frc_characterization
import frc_characterization.logger_analyzer.data_analyzer as analyzer
import frc_characterization.logger_analyzer.data_logger as logger
import frc_characterization.logger_gui as logger_gui
import frc_characterization.newproject as newproject

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem

langs = ("java", "cpp", "python")

controllers = ("spark", "talonsrx")

# TODO make logger automatically set itself to testtype
def newProject(testType, directory=None):
    newproject.main(testType)


def getAnalyzer(directory=None):
    analyzer.main(getcwd())


def loggerArm(directory=None):
    logger_gui.main(0, getcwd(), logger.TestRunner, test="Arm")


def analyzerArm(directory=None):
    analyzer.main(getcwd())


def loggerDrive(directory=None):
    logger_gui.main(0, getcwd(), logger.TestRunner, test="Drivetrain")


def analyzerDrive(directory=None):
    analyzer.main(getcwd())


def loggerElevator(directory=None):
    logger_gui.main(0, getcwd(), logger.TestRunner, test="Elevator")


def analyzerElevator(directory=None):
    analyzer.main(getcwd())


def loggerSimpleMotor(directory=None):
    logger_gui.main(0, getcwd(), logger.TestRunner, test="Simple")


def analyzerSimpleMotor(directory=None):
    analyzer.main(getcwd())


tool_dict = {
    "drive": {
        "new": partial(
            newProject,
            testType="Drivetrain",
        ),
        "logger": loggerDrive,
        "analyzer": getAnalyzer,
    },
    "arm": {
        "new": partial(newProject, testType="Arm"),
        "logger": loggerArm,
        "analyzer": getAnalyzer,
    },
    "elevator": {
        "new": partial(
            newProject,
            testType="Elevator",
        ),
        "logger": loggerElevator,
        "analyzer": getAnalyzer,
    },
    "simple-motor": {
        "new": partial(
            newProject,
            testType="Simple",
        ),
        "logger": loggerSimpleMotor,
        "analyzer": getAnalyzer,
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
