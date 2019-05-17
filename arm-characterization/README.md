Robot Drivetrain Characterization
=================================

This contains a test procedure that you can use to characterize a robot arm
so that you can more accurately control it.  The characterization will determine
best-fit parameters for the equation

![voltage balance equation](https://latex.codecogs.com/gif.latex?V_{applied}=kS&plus;kCos\cdot\cos{\theta}&plus;kV\cdot\dot{\theta}&plus;kA\cdot\ddot{\theta})

where theta is the angle of the arm as measured from horizontal.

The test procedure involves running your robot in autonomous mode several times
while the data logger program gathers data. It is important to stop autonomous
mode when the arm is about to hit something, as the programmed autonomous mode
will NOT stop the arm automatically.

Sample robot code is available in several different variations.

* [Java](robot-java)
* [Java TalonSRX](robot-java-talonsrx)
* [Python](robot-python)
* [Python TalonSRX](robot-python-talonsrx)

Prerequisites (PC)
------------------

Required to use the data_logger.py/data_analyzer.py scripts.

* Install Python 3.6 on your data gathering computer that will be connected to
  the robot's network
* Once finished, install pynetworktables, matplotlib, scipy, and statsmodels

On Windows the command to install pynetworktables, matplotlib, scipy, and statsmodels 
is as follows:

    py -3 -m pip install pynetworktables matplotlib scipy statsmodels

Prerequisites (Robot)
---------------------

Your robot must have an encoder attached to the arm to measure its
velocity.

If using a Python robot program, see the RobotPy installation documentation to
install software needed to deploy robot code, and how to install RobotPy on
your robot.

* http://robotpy.readthedocs.io/en/stable/install/index.html

If using a Java robot program, see the WPILIb screensteps documentation for
installing the necessary software on your computer.

* https://wpilib.screenstepslive.com/s/4485

Usage
-----

Preparation: make sure the code won't make your robot go crazy

1. Select one of the included robot programs, modify it to reflect your
   robot's arm configuration and encoder settings
2. Deploy the code to your robot
3. Ensure that pressing forward on a joystick moves the arm in the desired
   direction
4. If not, modify the 'inverted' flag in the code, repeat steps 2/3/4 until
   the arm moves as desired
5. Open SmartDashboard/Shuffleboard/OutlineViewer and ensure that the
   encoder values are incrementing positively by the correct distance in **degrees** 
   when you push the robot forward

Now you're ready to characterize your robot! On your data gathering computer,
launch data_logger.py (you can double-click it on Windows). Enter in your
team number or robot IP address when prompted.

Once the data logger has indicated that it has connected, do as prompted. Here's
what it will prompt you to do:

* Slow motion forward: Enable robot in autonomous mode, disable before the arm
  hits something
* Slow motion backward: Enable robot in autonomous mode, disable before the
  arm hits something
* Fast motion forward: Enable robot in autonomous mode, disable before the arm
  hits something
* Fast driving backward: Enable robot in autonomous mode, disable before the arm
  hits something

Once you have run the 4 autonomous modes, the data files will be written to
this directory and a window should pop up that plots the data for you and reports
your characterization values.
