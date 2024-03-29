#! /usr/bin/env python3

import os
from setuptools import setup, find_packages

PACKAGE = "riotctrl"
LICENSE = "MIT"
URL = "https://github.com/RIOT-OS/riotctrl"


def get_version(package):
    """Extract package version without importing file
    Importing cause issues with coverage,
        (modules can be removed from sys.modules to prevent this)
    Importing __init__.py triggers importing rest and then requests too

    Inspired from pep8 setup.py
    """
    with open(os.path.join(package, "__init__.py")) as init_fd:
        for line in init_fd:
            if line.startswith("__version__"):
                return eval(line.split("=")[-1])  # pylint:disable=eval-used
    return None


setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    description="RIOT Ctrl - A RIOT node python abstraction",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    author="Gaëtan Harter, Leandro Lanzieri, Martine S. Lenders",
    author_email="gaetan.harter@fu-berlin.de, "
    "leandro.lanzieri@haw-hamburg.de, "
    "m.lenders@fu-berlin.de",
    url=URL,
    license=LICENSE,
    download_url=URL,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: End Users/Desktop",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
    install_requires=["pexpect>=4.7", "psutil"],
    extras_require={"rapidjson": ["python-rapidjson"]},
    python_requires=">=3.5",
)
