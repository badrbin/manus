from setuptools import setup, find_packages

with open("requirements.txt") as f:
install_requires = f.read().strip().split("\n")

# get version from __version__ variable in manus/__init__.py
from manus import __version__ as version

setup(
name="manus",
version=version,
description="Custom integrations and validations for ERPNext 15",
author="Manus",
author_email="info@manus.im",
packages=find_packages(),
zip_safe=False,
include_package_data=True,
install_requires=install_requires
)
