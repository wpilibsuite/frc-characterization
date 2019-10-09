#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
if sys.version_info < (3, 0):
    print("You need to have Python 3 installed to run this script")
    exit(1)

import argparse, argcomplete

# Setting these functions up individually and importing conditionally is faster than importing everything at once
def armDataLogger():
    from arm_characterization.data_logger import main
    main()

def armDataAnalyzer():
    from arm_characterization.data_analyzer import main
    main()

def driveDataLogger():
    from drive_characterization.data_logger import main
    main()

def driveDataAnalyzer():
    from drive_characterization.data_analyzer import main
    main()

def elevatorDataLogger():
    from elevator_characterization.data_logger import main
    main()

def elevatorDataAnalyzer():
    from elevator_characterization.data_analyzer import main
    main()

tool_dict = {
    "logger": {"arm": armDataLogger, "drive": driveDataLogger, "elevator": elevatorDataLogger},
    "analyzer": {"arm": armDataAnalyzer, "drive": driveDataAnalyzer, "elevator": elevatorDataAnalyzer},
}

def main():

    parser = argparse.ArgumentParser(description="RobotPy characterization tools CLI")
    parser.add_argument("tool_type", choices=list(tool_dict.keys()),
        help="Tool type to use")
    parser.add_argument("mech_type", choices=list(list(tool_dict.values())[0].keys()),
        help="Mechanism type to with that tool")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    tool_dict[args.tool_type][args.mech_type]()

if __name__ == "__main__":

    main()
