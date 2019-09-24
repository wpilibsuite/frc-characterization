import drive_characterization.data_analyzer
import drive_characterization.data_logger
import arm_characterization.data_analyzer
import arm_characterization.data_logger
import elevator_characterization.data_analyzer
import elevator_characterization.data_logger

import argparse
import argcomplete

# Setting these functions up individually and importing conditionally is faster than importing everything at once
# def armDataLogger():
#     from arm_characterization.data_logger import main
#     main()

# def armDataAnalyzer():
#     from arm_characterization.data_analyzer import main
#     main()


def armDataLogger():
    arm_characterization.data_logger.main()


def armDataAnalyzer():
    arm_characterization.data_analyzer.main()


def driveDataLogger():
    drive_characterization.data_logger.main()


def driveDataAnalyzer():
    drive_characterization.data_analyzer.main()


def elevatorDataLogger():
    elevator_characterization.data_logger.main()


def elevatorDataAnalyzer():
    elevator_characterization.data_analyzer.main()


# def elevatorDataLogger():
#     from elevator_characterization.data_logger import main
#     main()

# def elevatorDataAnalyzer():
#     from elevator_characterization.data_analyzer import main
#     main()

tool_dict = {
    "logger": {
        "arm": armDataLogger,
        "drive": driveDataLogger,
        "elevator": elevatorDataLogger,
    },
    "analyzer": {
        "arm": armDataAnalyzer,
        "drive": driveDataAnalyzer,
        "elevator": elevatorDataAnalyzer,
    },
    # "logger": {"arm": armDataLogger, "drive": driveDataLogger, "elevator": elevatorDataLogger},
    # "analyzer": {"arm": armDataAnalyzer, "drive": driveDataAnalyzer, "elevator": elevatorDataAnalyzer},
}


def main():

    parser = argparse.ArgumentParser(description="RobotPy characterization tools CLI")
    parser.add_argument(
        "tool_type", choices=list(tool_dict.keys()), help="Tool type to use"
    )
    parser.add_argument(
        "mech_type",
        choices=list(list(tool_dict.values())[0].keys()),
        help="Mechanism type to with that tool",
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    tool_dict[args.tool_type][args.mech_type]()


if __name__ == "__main__":

    main()
