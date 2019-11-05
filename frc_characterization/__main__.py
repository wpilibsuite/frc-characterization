# Shim to run the CLI entry point as an ordinary python module for those
# who are having trouble adding python scripts to PATH.

import frc_characterization.cli as cli


def main():

    cli.main()


if __name__ == "__main__":

    main()
