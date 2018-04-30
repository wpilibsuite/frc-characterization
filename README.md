RobotPy Drivetrain Characterization
===================================

This contains a test procedure that you can use to characterize your drivetrain
so that you can more accurately control and simulate it.

The test procedure involves running your robot in autonomous mode several times
while the data logger program gathers data. It is important to stop autonomous
mode when the robot is about to hit something, as the programmed autonomous mode
will NOT stop your robot automatically.

This robot program also has RobotPy physics support, so you can run the tests
in simulation if you want to see what the autonomous mode does! Unfortunately,
it does not model battery voltage realistically, so you will only get a kv value
from the simulation.

Prerequisites
-------------

Your robot must have encoders attached to the drivetrain to measure the robot's
velocity.

Installation:

1. Install RobotPy on your robot (see http://robotpy.readthedocs.io/en/stable/install/robot.html)
2. Install Python 3.6, scipy, matplotlib and pyfrc on your data gathering computer that
   will be connected to the robot's network
   
On Windows the command to install matplotlib/scipy/pyfrc are as follows:

    py -3 -m pip install pyfrc matplotlib scipy

Usage
-----

Preparation: make sure the code won't make your robot go crazy

1. Modify robot.py to reflect your robot's drivetrain and encoder settings
2. Deploy the code to your robot
3. Ensure that pressing forward on a joystick makes your robot drive forward
4. If not, modify the 'inverted' flags in the code, repeat steps 2/3/4 until
   the robot drives forward
5. Open SmartDashboard/Shuffleboard/OutlineViewer and ensure that the
   l_encoder and r_encoder values are incrementing positively the correct
   distance when you push the robot forward
   
Now you're ready to characterize your robot! On your data gathering computer,
launch datalogger.py (you can double-click it on Windows). Enter in your
team number or robot IP address when prompted.

Once the datalogger has indicated that it has connected, do as prompted. Here's
what it will prompt you to do:

* Slow driving forward: Enable robot in autonomous mode, disable before the robot
  hits something
* Slow driving backward: Enable robot in autonomous mode, disable before the
  robot hits something
* Fast driving forward: Enable robot in autonomous mode, disable before the robot
  hits something
* Fast driving backward: Enable robot in autonomous mode, disable before the robot
  hits something

Once you have ran the 4 autonomous modes, the data files will be written to
this directory and a window should pop up that plots the data for you.

Next steps
----------

You can plug the generated kv/ka/vintercept parameters into the TankModel for
your robot.

Finally, help the rest of the FRC community! Post your json data + drivetrain
characteristics at https://www.chiefdelphi.com/forums/showthread.php?t=161539
