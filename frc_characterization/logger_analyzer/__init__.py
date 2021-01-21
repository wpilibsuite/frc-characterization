from mako.template import Template

import os
from importlib import import_module
import pathlib
import zipfile


# TODO: Replace with Python 3.9's importlib.resources.files() when it becomes min version
def files(package):
    spec = import_module(package).__spec__
    if spec.submodule_search_locations is None:
        raise TypeError("{!r} is not a package".format(package))

    package_directory = pathlib.Path(spec.origin).parent
    try:
        archive_path = spec.loader.archive
        rel_path = package_directory.relative_to(archive_path)
        return zipfile.Path(archive_path, str(rel_path) + "/")
    except Exception:
        pass
    return package_directory


def gen_robot_code(config):
    path = files(__name__).joinpath("templates")
    with open(os.path.join(path, "Robot.java.mako"), "r") as template:
        return Template(template.read()).render(**config)


def gen_build_gradle(team):
    path = files(__name__).joinpath("templates")
    with open(os.path.join(path, "build.gradle.mako"), "r") as template:
        return Template(template.read()).render(team=team)
