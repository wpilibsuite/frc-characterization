# The CLI entry point for the characterization toolsuite.

import argparse
from os import getcwd
from sys import argv

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
from consolemenu import SelectionMenu

langs = ("java", "cpp", "python")

controllers = ("spark", "talonsrx")


def newProject(dir, mech):
    newproject.main(mech)


def loggerArm(dir):
    logger_gui.main(0, getcwd(), arm_logger.TestRunner)


def analyzerArm(dir):
    arm_analyzer.main(getcwd())


def loggerDrive(dir):
    logger_gui.main(0, getcwd(), drive_logger.TestRunner)


def analyzerDrive(dir):
    drive_analyzer.main(getcwd())


def loggerElevator(dir):
    logger_gui.main(0, getcwd(), elevator_logger.TestRunner)


def analyzerElevator(dir):
    elevator_analyzer.main(getcwd())


def loggerSimpleMotor(dir):
    logger_gui.main(0, getcwd(), simplemotor_logger.TestRunner)


def analyzerSimpleMotor(dir):
    simplemotor_analyzer.main(getcwd())


tool_dict = {
    "drive": {
        "new": lambda dir: newProject(dir, frc_characterization.drive_characterization),
        "logger": loggerDrive,
        "analyzer": analyzerDrive,
    },
    "arm": {
        "new": lambda dir: newProject(dir, frc_characterization.arm_characterization),
        "logger": loggerArm,
        "analyzer": analyzerArm,
    },
    "elevator": {
        "new": lambda dir: newProject(
            dir, frc_characterization.elevator_characterization
        ),
        "logger": loggerElevator,
        "analyzer": analyzerElevator,
    },
    "simple-motor": {
        "new": lambda dir: newProject(
            dir, frc_characterization.simplemotor_characterization
        ),
        "logger": loggerSimpleMotor,
        "analyzer": analyzerSimpleMotor,
    },
}


def main():

    if len(argv) < 2:
        main_menu = SelectionMenu(
            tool_dict.keys(), "What type of mechanism are you characterizing?",
        )
        main_menu.show()
        main_menu.join()
        mech_type = main_menu.selected_item.text

        if main_menu.is_selected_item_exit():
            exit()

        submenu = SelectionMenu(
            list(tool_dict.values())[0].keys(), "What tool do you want to use?",
        )
        submenu.show()
        submenu.join()
        tool_type = submenu.selected_item.text

        if submenu.is_selected_item_exit():
            exit()

        tool_dict[mech_type][tool_type](None)
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
        tool_dict[args.mech_type][args.tool_type](args.project_directory)


if __name__ == "__main__":

    main()
