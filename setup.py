import setuptools

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README_pypi.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='robotpy-characterization',
    version='0.1.9',
    author='Eli Barnett, Dustin Spicuzza',
    author_email='emichaelbarnett@gmail.com, dustin@virtualroadside.com',
    description='RobotPy Characterization Library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=[
        'arm_characterization',
        'drive_characterization',
        'elevator_characterization',
        'logger_gui',
        'cli',
        'utils',
        'newproject',
        'robot'
    ],
    entry_points={'console_scripts': ['robotpy-characterization = cli.cli:main']},
    url='https://github.com/robotpy/robot-characterization',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'control',
        'frccontrol',
        'matplotlib',
        'pynetworktables>=2018.1.2',
        'statsmodels',
        'argcomplete',
        'console-menu',
        'mako',
    ],
    python_requires='>=3.7',
    include_package_data=True
)
