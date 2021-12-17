#!/usr/bin/python

import os
from enum import Enum, unique
from subprocess import getoutput
from typing import Optional

from funtoo.boot.config import BootConfigFile
from funtoo.boot.cpu import AMD, CPU, Intel, ScanPaths


class fstabInfo:
	def __init__(self, root_path):
		self.root_path = root_path
		self.devices = {}
		self.mountpoints = {}
		fn = open(os.path.join(self.root_path, "/etc/fstab".lstrip("/")), "r")
		for line in fn.readlines():
			line = line[0 : line.find("#")]
			split = line.split()
			if len(split) != 6:
				continue
			self.devices[split[0]] = split
			self.mountpoints[split[1]] = split
		fn.close()

	def hasEntry(self, fs):
		return fs in self.mountpoints

	def getFilesystemOfDevice(self, d):
		if d in self.devices:
			return self.devices[d][2]
		return ""

	def getRootDevice(self):
		return self.mountpoints["/"][0] if "/" in self.mountpoints else ""

	def getRootMountFlags(self):
		return self.mountpoints["/"][3] if "/" in self.mountpoints else ""


def get_scanpaths(boot_config: BootConfigFile) -> ScanPaths:
	sections = boot_config.getSections()
	scanpaths = set()
	for sect in sections:
		paths = set(boot_config.item(sect, "scan").split())
		scanpaths |= paths
	return scanpaths


def get_cpu_vendor() -> str:
	return getoutput("LANG=C LC_ALL=C /usr/bin/lscpu | grep ^Vendor").split(" ").pop()


@unique
class CPUEnum(Enum):
	GenuineIntel = Intel
	AuthenticAMD = AMD


def get_cpu_instance(boot_config: BootConfigFile) -> Optional[CPU]:
	try:
		vendor = get_cpu_vendor()
		cpu = CPUEnum[vendor].value
		scanpaths = get_scanpaths(boot_config)
		return cpu(scanpaths)
	except KeyError:
		return None


# vim: ts=4 sw=4 noet
