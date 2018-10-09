# -*- coding: ascii -*-

import os
import shlex
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

from funtoo.boot.extension import Extension, ExtensionError


def getExtension(config):
	return GRUBLegacyExtension(config)


class GRUBLegacyExtension(Extension):

	def __init__(self,config):
		Extension.__init__(self,config)
		self.fn = "{path}/{dir}/{file}".format(path = self.config["boot/path"], dir = self.config["grub-legacy/dir"], file = self.config["grub-legacy/file"])
		self.bootitems = []
		
	def initialize(self):
		self.grub_root = self.DeviceGRUB(self.DeviceOfFilesystem(self.config["boot/path"]))
		if self.grub_root is None:
			self.msgs.append(["fatal", "Could not determine device of filesystem using grub-probe"])
			return False

	def isAvailable(self):
		return True

	def generateOtherBootEntry(self, l, sect):
		mytype = self.config["{s}/type".format(s=sect)].lower()
		if mytype in ["dos", "msdos"]:
			mytype = "dos"
		elif mytype in ["windows", "windows 2000", "win2000", "windows xp", "winxp"]:
			mytype = "winxp"
		elif mytype in ["windows vista", "vista"]:
			mytype = "vista"
		elif mytype in ["windows 7", "win7"]:
			mytype = "win7"
		elif mytype in [ "windows 8", "win8"]:
			mytype = "win8"
		elif mytype in ["haiku", "haiku os"]:
			mytype = "haiku"
		else:
			self.msgs.append(["fatal","Unrecognized boot entry type \"{type}\"".format(type = mytype)])
			return False
		params = self.config["{s}/params".format(s = sect)].split()
		myroot = self.r.GetParam(params,"root=")
		# TODO check for valid root entry
		l.append("title {s}".format(s=sect))
		self.bootitems.append(sect)
		mygrubroot = self.DeviceGRUB(myroot)
		if mygrubroot is None:
			self.msgs.append(["fatal", "Couldn't determine root device using grub-probe"])
			return False
		if mytype == "haiku":
			l.append("  rootnoverify {dev}".format(dev = mygrubroot))
		else :
			l.append("  root {dev}".format(dev = mygrubroot))
		if mytype in ["win7", "win8"]:
			l.append("  chainloader +4")
		elif mytype in ["vista", "dos", "winxp", "haiku"]:
			l.append("  chainloader +1")
		l.append("")
		return True

	def DeviceOfFilesystem(self,fs):
		return self.Guppy(" --target=device {f}".format(f=fs))

	def Guppy(self,argstring, fatal=True):
		gprobe = "/usr/sbin/grub-probe"
		if not os.path.exists(gprobe):
			gprobe = "/sbin/grub-probe"
		if not os.path.exists(gprobe):
			raise ExtensionError("couldn't find grub-probe")
		cmd = shlex.split("{gcmd} {args}".format(gcmd = gprobe, args = argstring))
		cmdobj = Popen(cmd, bufsize = -1, stdout = PIPE, stderr = STDOUT, shell = False)
		output = cmdobj.communicate()
		if cmdobj.poll() != 0:
			print("ERROR calling {cmd} {args}, Output was:\n{out}".format(cmd = gprobe, args = argstring, out = output[0].decode()))
			return None
		else:
			return output[0].decode().strip("\n")
	
	def DeviceGRUB(self, dev):
		out = self.Guppy(" --device {d} --target=drive".format(d=dev))
		# Convert GRUB "count from 1" (hdx,y) format to legacy "count from 0" format
		if out is None:
			return None
		mys = out[1:-1].split(",")
		partnum = mys[1]
		if partnum[:-1] == "msdos":
			partnum = partnum[:-1]
		try:
			partnum = int(partnum)
		except ValueError:
			print("ERROR: could not parse: %s" % out)
			return None
		mys = (mys[0], partnum - 1)
		out = "({d},{p})".format(d=mys[0], p=mys[1])
		return out
	
	def generateBootEntry(self, l, sect, kname, kext):
		
		ok = True
		mytype = self.config["{s}/type".format(s=sect)]
		label = self.r.GetBootEntryString(sect, kname)
		
		l.append("title {name}".format(name=label))
		self.bootitems.append(label)
		
		# Get kernel and params
		kpath = self.r.strip_mount_point(kname)
		params = []
		c = self.config
		if c.hasItem("boot/terminal") and c["boot/terminal"] == "serial":
			params += [
				"console=tty0",
				"console=ttyS%s,%s%s%s" % (c["serial/unit"], c["serial/speed"], c["serial/parity"][0], c["serial/word"])
			]
		for param in self.config.item(sect, "params").split():
			if param not in params:
				params.append(param)
		ok, myroot = self.r.calculate_rootfs_for_section(params)
		if not ok:
			return False
		ok, fstype = self.r.calculate_filesystem_for_section(params)
		if not ok:
			return False

		mygrubroot = self.DeviceGRUB(self.DeviceOfFilesystem(self.config["boot/path"]))
		if mygrubroot is None:
			self.msgs.append(["fatal", "Could not determine device of filesystem using grub-probe"])
			return False

		# print out our grub-ified root setting
		l.append("  root {dev}".format(dev=mygrubroot))

		# Get initrds
		initrds = self.config.item(sect, "initrd")
		initrds = self.r.find_initrds(initrds, kname, kext)
		
		xenpath = None
		xenparams = []
		# Populate xen variables if type is xen
		if mytype == "xen":
			xenkernel = self.config["{s}/xenkernel".format(s=sect)]
			# Add leading / if needed
			if not xenkernel.startswith("/"):
				xenkernel = "/{xker}".format(xker=xenkernel)
			xenpath = self.r.strip_mount_point(xenkernel)
			xenparams = self.config["{s}/xenparams".format(s=sect)].split()

		# Append kernel lines based on type
		
		if mytype == "xen":
			l.append("  kernel {xker} {xparams}".format(xker=xenpath, xparams=" ".join(xenparams)))
			l.append("  module {ker} {params}".format(ker=kpath, params=" ".join(params)))
			for initrd in initrds:
				l.append("  module {initrd}".format(initrd = self.r.strip_mount_point(initrd)))
		else :
			l.append("  kernel {k} {par}".format(k=kpath, par=" ".join(params)))
			for initrd in initrds:
				l.append("  initrd {rd}".format(rd=self.r.strip_mount_point(initrd)))

		l.append("")

		return ok
	
	def generateConfigFile(self):
		l = []
		ok = True
		# pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries
		
		ok, self.defpos, self.defname = self.r.GenerateSections(l, self.generateBootEntry, self.generateOtherBootEntry)
		if not ok:
			return False, l
		c = self.config
		if c.hasItem("boot/terminal") and c["boot/terminal"] == "serial":
			self.msgs.append(["warn", "Configured for SERIAL input/output."])
			l = [
					"serial --unit=%s --speed=%s --word=%s --parity=%s --stop=%s" % (
					c["serial/unit"], c["serial/speed"], c["serial/word"], c["serial/parity"], c["serial/stop"]),
					"terminal %s serial console" % "--timeout=%s" % c["boot/timeout"] if c.hasItem("boot/timeout") else "",
					"default {pos}".format(pos=self.defpos),
					""
				] + l
		else:
			l = [
					self.config.condFormatSubItem("boot/timeout", "timeout {s}"),
					"default {pos}".format(pos=self.defpos),
					""
				] + l
		
		return ok, l
