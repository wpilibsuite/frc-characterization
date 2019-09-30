import setuptools

setuptools.setup(
    name="robotpy-characterization",
    version="0.0.6",
    author="Eli Barnett, Dustin Spicuzza",
    author_email="emichaelbarnett@gmail.com, dustin@virtualroadside.com",
    description="RobotPy Characterization Library",
    packages=[
        "arm_characterization",
        "drive_characterization",
        "elevator_characterization",
        "cli",
        "utils",
        "newproject"
    ],
    entry_points={"console_scripts": ["robotpy-characterization = cli.cli:main"]},
    url="https://github.com/robotpy/robot-characterization",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "control",
        "frccontrol",
        "matplotlib",
        "pynetworktables>=2018.1.2",
        "statsmodels",
        "argcomplete",
        "console-menu",
        "mako",
    ],
    python_requires=">=3.4",
    include_package_data=True
)
