import setuptools
import cli.cli

setuptools.setup(
    name="robotpy-characterization",
    version="0.0.1",
    author="Eli Barnett",
    author_email="emichaelbarnett@gmail.com",
    description="RobotPy Characterization Library",
    packages=[
        "arm_characterization",
        "drive_characterization",
        "elevator_characterization",
        "cli",
        "utils",
    ],
    entry_points={"console_scripts": ["robotpy-characterization = cli.cli:main"]},
    url="https://github.com/robotpy/robot-characterization",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "frccontrol",
        "matplotlib",
        "pynetworktables>=2018.1.2",
        "statsmodels",
        "argcomplete",
    ],
    python_requires=">=3.4",
)
