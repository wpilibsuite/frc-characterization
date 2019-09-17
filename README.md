Robot Characterization Toolsuite
================================

This is a toolsuite for characterization of FRC robot mechanisms.  The characterization tools consist
of a python application that runs on the user's PC, and matching robot code that runs on the user's
robot.  The PC application will send control signals to the robot over network tables, while the robot
sends data back to the application.  The application then processes the data and determines 
characterization parameters for the user's robot mechanism, as well as producing diagnostic plots.  Data
can be saved (in JSON format) for future use, if desired.

Included Characterization Tools
-------------------------------

The robot characterization toolsuite currently supports chracterization for:

- Drivetrains
- Arms
- Elevators

Feature requests for additional characterization tools are welcome.  Also note that many
mechanisms can be characterized by simply adapting the existing code in this library.

Instructions for using the individual tools can be found in their respective project directories. 
The procedures are highly-similar for all of the tools.

Prerequisites (PC)
------------------

The following is required to use the data_logger.py/data_analyzer.py scripts for all
of the characterization tools included in this repository:

* Install Python 3.6 on your data gathering computer that will be connected to
  the robot's network
* Once finished, install pynetworktables, matplotlib, scipy, frccontrol, and statsmodels

On Windows the command to install pynetworktables, matplotlib, scipy, frccontrol and statsmodels 
is as follows:

    py -3 -m pip install pynetworktables matplotlib scipy frccontrol statsmodels

Prerequisites (Robot)
---------------------

If using a Python robot program, see the RobotPy installation documentation to
install software needed to deploy robot code, and how to install RobotPy on
your robot.

* http://robotpy.readthedocs.io/en/stable/install/index.html

If using a Java or C++ robot program, see the WPILIb screensteps documentation for
installing the necessary software on your computer.

* https://wpilib.screenstepslive.com/s/4485

Contributing new changes
------------------------

This is intended to be a project that all members of the FIRST community can
quickly and easily contribute to. If you find a bug, or have an idea that you
think others can use:

1. [Fork this git repository](https://github.com/robotpy/robot-characterization/fork) to your github account
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push -u origin my-new-feature`)
5. Create new Pull Request on github

License
-------

All code in this repository is available under the Apache v2 license.

Authors
-------

Dustin Spicuzza (dustin@virtualroadside.com)

Eli Barnett (emichaelbarnett@gmail.com)