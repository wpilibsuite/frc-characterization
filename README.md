frc-characterization has been archived. The features it provided are now a part of sysid - https://github.com/AustinShalit/frc-characterization.git

# Robot Characterization Toolsuite

This is a toolsuite for characterization of FRC robot mechanisms.  The characterization tools consist of a python application that runs on the user's PC, and matching robot code that runs on the user's robot.  The PC application will send control signals to the robot over network tables, while the robot sends data back to the application.  The application then processes the data and determines  characterization parameters for the user's robot mechanism, as well as producing diagnostic plots.  Data can be saved (in JSON format) for future use, if desired.

For in-depth documentation, see the project's [frc-docs page](https://docs.wpilib.org/en/stable/docs/software/wpilib-tools/robot-characterization/introduction.html).

## Contributing new changes

This is intended to be a project that all members of the FIRST community can quickly and easily contribute to. If you find a bug, or have an idea that you think others can use:

1. [Fork this git repository](https://github.com/wpilibsuite/frc-characterization/fork) to your GitHub account.
2. Create your feature branch (`git checkout -b my-new-feature`).
3. Make changes.
4. Install the black formatter (`pip install black --upgrade`), and run it (`black ./` when your working directory is this repo). If your PR is failing because of formatting issues and your local formatter says everything is good then black is likely out of date.
5. Commit your changes (`git commit -am 'Add some feature'`).
6. Push to the branch (`git push -u origin my-new-feature`).
7. Create new Pull Request on github.

## License

All code in this repository is available under the Apache v2 license.
