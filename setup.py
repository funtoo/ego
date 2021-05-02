import os
import setuptools

from subpop.pkg import Packager, SubPopSetupInstall

pkgr = Packager()

if os.path.exists("README.rst"):
	with open("README.rst", "r") as fh:
		long_description = fh.read()
else:
	long_description = ""

setuptools.setup(
	name="ego",
	version="3.0.0",
	author="Daniel Robbins",
	author_email="drobbins@funtoo.org",
	description="Funtoo Personality Tool",
	long_description=long_description,
	long_description_content_type="text/x-rst",
	url="https://code.funtoo.org/bitbucket/projects/CORE/repos/ego/browse",
	scripts=["bin/ego"],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)" "Operating System :: POSIX :: Linux",
	],
	python_requires=">=3.7",
	install_requires=["subpop >= 0.4.1", "requests", "appi"],
	packages=setuptools.find_packages(),
	data_files=pkgr.generate_data_files(),
	cmdclass={"install": SubPopSetupInstall},
)
