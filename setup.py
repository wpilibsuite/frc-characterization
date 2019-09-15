import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="characterization-tool",
    version="1.0.0",
    author="Eli Barnett, Dustin Spicuzza",
    author_email="dustin@virtualroadside.com",
    packages=["drive_characterization", "arm_characterization"],
    scripts=["cli/characterization-tool"],
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        "argcomplete"
    ],
    python_requires=">=3.4",
)
