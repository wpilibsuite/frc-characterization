#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
if sys.version_info < (3, 0):
    print("You need to have Python 3 installed to run this script")
    exit(1)

import argparse, argcomplete

from arm_characterization.data_logger import main as armDataLogger
from arm_characterization.data_analyzer import main as armDataAnalyzer

from drive_characterization.data_logger import main as driveDataLogger
from drive_characterization.data_analyzer import main as driveDataAnalyzer

tool_dict = {
    "logger": {"arm": armDataLogger, "drive": driveDataLogger},
    "analyzer": {"arm": armDataAnalyzer, "drive": driveDataAnalyzer},
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
