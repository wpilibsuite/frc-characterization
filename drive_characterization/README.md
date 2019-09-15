Robot Drivetrain Characterization
=================================

This contains a test procedure that you can use to characterize your drivetrain
so that you can more accurately control and simulate it.  The characterization will 
determine the best-fit parameters for the equation

![voltage balance equation](https://latex.codecogs.com/gif.latex?V_{applied}=kS&plus;kV\cdot\dot{d}&plus;kA\cdot\ddot{d})

where d is the distance traveled by the robot in feet.

The test procedure involves running your robot in autonomous mode several times
while the data logger program gathers data. It is important to stop autonomous
mode when the robot is about to hit something, as the programmed autonomous mode
will NOT stop your robot automatically.

Sample robot code is available in several different variations.

* [Java](robot-java)
* [Java TalonSRX](robot-java-talonsrx)
* [Python](robot-python)
* [Python TalonSRX](robot-python-talonsrx)
* [C++](robot-cpp)
* [C++ TalonSRX](robot-cpp-talonsrx)

Python robot code also has RobotPy physics support, so you can run the tests in
simulation if you want to see what the autonomous mode does! Unfortunately, it
does not model battery voltage realistically, so you will only get a kv value
from the simulation.

Prerequisites (PC)
------------------

Required to use the data_logger.py/data_analyzer.py scripts.

* Install Python 3.6 on your data gathering computer that will be connected to
  the robot's network
* Install `characterization-tool` from PyPI. If you're on Windows, run `py -3 -m pip install characterization-tool`

Prerequisites (Robot)
---------------------

Your robot must have encoders attached to the drivetrain to measure the robot's
position and velocity.

If using a Python robot program, see the RobotPy installation documentation to
install software needed to deploy robot code, and how to install RobotPy on
your robot.

* http://robotpy.readthedocs.io/en/stable/install/index.html

If using a Java or C++ robot program, see the WPILIb screensteps documentation for
installing the necessary software on your computer.

* https://wpilib.screenstepslive.com/s/4485

Usage
-----

Recording
=========

Preparation: make sure the code won't make your robot go crazy

1. Select one of the included robot programs, modify it to reflect your
   robot's drivetrain and encoder settings
2. Deploy the code to your robot
3. Ensure that pressing forward on a joystick makes your robot drive forward
4. If not, modify the 'inverted' flags in the code, repeat steps 2/3/4 until
   the robot drives forward
5. Open SmartDashboard/Shuffleboard/OutlineViewer and ensure that the
   l_encoder and r_encoder values are incrementing positively the correct
   distance in **feet** when you push the robot forward

Now you're ready to characterize your robot! On your data gathering computer,
run `characterization-tool logger drive`. Enter in your
team number or robot IP address when prompted.

Once the data logger has indicated that it has connected, do as prompted. Here's
what it will prompt you to do:

* Slow driving forward: Enable robot in autonomous mode, disable before the robot
  hits something
* Slow driving backward: Enable robot in autonomous mode, disable before the
  robot hits something
* Fast driving forward: Enable robot in autonomous mode, disable before the robot
  hits something
* Fast driving backward: Enable robot in autonomous mode, disable before the robot
  hits something

Once you have ran the 4 autonomous modes, the data will be recorded in a json file
in this directory.

Analysis
========

Once you have recorded your data, launch the analysis GUI by running `characterization-tool analyzer drive`.
This will open a GUI that will analyze your data.  The left half of this GUI, labeled 
"Feedforward Analysis," will perform the linear regression and generate the aforementioned 
coefficients.

To calculate the characterization coefficients, first select the data file, and then click 
the "Analyze Data" button.  Various diagnostic plots will then become available, and the 
characterization coefficients and the r-squared for the fit will be displayed.  If problems 
are encountered, try modifying the minimum motion threshold or the window size for the 
acceleration calculation.

The right half of the GUI, labeled "Feedback Analysis," will generate optimal feedback 
gains for a simple PD controller via a Linear-Quadratic Regulator (LQR).  While the calculation 
is straightforward, the units of the gains depend critically on the controller setup - more 
detailed documentation on ensuring the correctness of units will be provided at a later date.

Next steps
----------

If using RobotPy and the pyfrc robot simulator, you can plug the generated
kv/ka/vintercept parameters into the TankModel for your robot for a more
realistic simulation experience.

Refer to the [original drivetrain characterization paper](https://www.chiefdelphi.com/media/papers/3402)
for ideas on how to use these empirically measured constants to improve control
of your drivetrain.

Finally, help the rest of the FRC community! Post your raw json data + drivetrain
characteristics at https://www.chiefdelphi.com/forums/showthread.php?t=161539
