from setuptools import setup, find_packages

with open("requirements.txt") as f:
.gitignore install_requires = f.read().strip().split("\n")

# get version from __version__ variable in manus/__init__.py
from manus import __version__ as version

setup(
.gitignore name="manus",
.gitignore version=version,
.gitignore description="Custom integrations and validations for ERPNext 15",
.gitignore author="Manus",
.gitignore author_email="info@manus.im",
.gitignore packages=find_packages(),
.gitignore zip_safe=False,
.gitignore include_package_data=True,
.gitignore install_requires=install_requires
)
