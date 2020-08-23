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
from frc_characterization.newproject import Tests

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem

langs = ("java", "cpp", "python")

controllers = ("spark", "talonsrx")


def new_project(testType, directory=None):
    newproject.main(testType)


def get_analyzer(directory=None):
    analyzer.main(directory or getcwd())


def get_logger(testType, directory=None):
    logger_gui.main(0, directory or getcwd(), logger.TestRunner, test=testType)


tool_dict = {
    "drive": {
        "new": partial(new_project, testType=Tests.DRIVETRAIN),
        "logger": partial(get_logger, testType=Tests.DRIVETRAIN),
        "analyzer": get_analyzer,
    },
    "arm": {
        "new": partial(new_project, testType=Tests.ARM),
        "logger": partial(get_logger, testType=Tests.ARM),
        "analyzer": get_analyzer,
    },
    "elevator": {
        "new": partial(new_project, testType=Tests.ELEVATOR),
        "logger": partial(get_logger, testType=Tests.ELEVATOR),
        "analyzer": get_analyzer,
    },
    "simple-motor": {
        "new": partial(new_project, testType=Tests.SIMPLE_MOTOR),
        "logger": partial(get_logger, testType=Tests.SIMPLE_MOTOR),
        "analyzer": get_analyzer,
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
