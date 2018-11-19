#!/usr/bin/python

import os

class fstabInfo:
	
	def __init__(self, root_path):
		self.root_path = root_path
		self.devices = {}
		self.mountpoints = {}
		fn = open(os.path.join(self.root_path, "/etc/fstab".lstrip("/")), "r")
		for line in fn.readlines():
			line = line[0:line.find("#")]
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
		return self.mountpoints['/'][0] if '/' in self.mountpoints else ""
	
	def getRootMountFlags(self):
		return self.mountpoints['/'][3] if '/' in self.mountpoints else ""

# vim: ts=4 sw=4 noet
