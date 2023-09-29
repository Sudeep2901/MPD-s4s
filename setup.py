from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in s4s/__init__.py
from s4s import __version__ as version

setup(
	name="s4s",
	version=version,
	description="Food Processing",
	author="Mannlowe Information Service Pvt. Ltd.",
	author_email="shrikant.pawar@mannlowe.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
