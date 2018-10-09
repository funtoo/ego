# -*- coding: ascii -*-

import os
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

from funtoo.boot.extension import Extension


def getExtension(config):
	return LILOExtension(config)


class LILOExtension(Extension):
	
	def __init__(self, config):
		Extension.__init__(self, config)
		self.fn = self.config["lilo/file"]
		self.lilo_cmd = self.config["lilo/bin"]
		self.bootitems = []
	
	def isAvailable(self):
		ok = True
		if not os.path.exists(self.lilo_cmd):
			self.msgs.append(["fatal", "{cmd}, required for boot/generate = lilo, does not exist".format(cmd=self.lilo_cmd)])
			ok = False
		return ok
	
	def updateBootLoader(self):
		""" Runs lilo command to update the boot loader map """
		ok = True
		self.msgs.append(["info", "Now running {lilo}".format(lilo=self.lilo_cmd)])
		
		cmdobj = Popen(self.lilo_cmd, bufsize=-1, stdout=PIPE, stderr=STDOUT, shell=False)
		output = cmdobj.communicate()
		if cmdobj.poll() != 0:
			self.msgs.append(["fatal", "Error running {cmd} :\n{out}".format(cmd=self.lilo_cmd, out=output[0].decode())])
			return False
		else:
			self.msgs.append(["info", "Successfully ran {cmd}. Output was :\n\n{out}\n".format(cmd=self.lilo_cmd, out=output[0].decode())])
			return ok
	
	def generateOtherBootEntry(self, l, sect):
		ok = True
		
		# Name can not be longer than 15 characters
		if len(sect) > 15:
			self.msgs.append(["fatal",
							"'{name}' is too long. Section names in /etc/boot.conf for non-linux OS must not exceed 15 characters when using lilo".format(
								name=sect)])
			return False
		
		self.bootitems.append(sect)
		params = self.config["{s}/params".format(s=sect)].split()
		myroot = self.r.GetParam(params, "root=")
		
		l.append("")
		l.append("other={dev}".format(dev=myroot))
		
		# Make sure we change any spaces in name to "_". Lilo doesn't like spaces.
		l.append("	label=\"{name}\"".format(name=sect.replace(" ", "_")))
		
		return ok
	
	def generateBootEntry(self, l, sect, kname, kext):
		
		ok = True
		
		# Type 'xen' isn't supported in lilo
		if self.config["{s}/type".format(s=sect)] == "xen":
			self.msgs.append(["fatal", "Type 'xen' is not supported in lilo"])
			return False
		
		# 'Label' has a character limit, not kernel name.
		if len(os.path.basename(sect)) > 15:
			self.msgs.append(["fatal", "'{name}' is too long. Kernel names must not exceed 15 characters when using lilo".format(name=(os.path.basename(kname)))])
			return False
		
		l.append("")
		self.bootitems.append(kname)
		l.append("image={k}".format(k=kname))
		c = self.config
		params = []
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
		ok, myfstype = self.r.calculate_filesystem_for_section(params)
		if not ok:
			return False
		
		self.r.ZapParam(params, "root=")
		
		l += [
			"	label=\"{name}\"".format(name=sect.replace(" ", "_")),
			"	read-only",
			"	root={dev}".format(dev=myroot),
			"	append=\"{par}\"".format(par=" ".join(params))
		]
		initrds = self.config.item(sect, "initrd")
		initrds = self.r.find_initrds(initrds, kname, kext)
		for initrd in initrds:
			l.append("  initrd={rd}".format(self.r.RelativePathTo(initrd, "/boot")))
		
		return ok
	
	def generateConfigFile(self):
		l = []
		c = self.config
		ok = True
		
		# Warn if no boot entry.
		if c.hasItem("boot/bootdev"):
			l.append("boot={dev}".format(dev=c["boot/bootdev"]))
		else:
			self.msgs.append(["warn",
							"No 'bootdev' entry specified in section 'boot'. Lilo will install itself to the current root partition. See `man 5 boot.conf` for more info"])
		
		# Append global lilo params
		for gparam in c["lilo/gparams"].split():
			l.append(gparam)
		
		# Pass our boot entry generator function to GenerateSections, and everything is taken care of for our boot entries
		
		ok, self.defpos, self.defname = self.r.GenerateSections(l, self.generateBootEntry, self.generateOtherBootEntry)
		if not ok:
			return ok, l
		
		# Lilo's config uses 1/10 secs.
		if c.hasItem("boot/timeout"):
			timeout = "timeout={time}".format(time=int(c["boot/timeout"]) * 10)
		else:
			timeout = ""
		
		if c.hasItem("boot/terminal") and c["boot/terminal"] == "serial":
			self.msgs.append(["warn", "Configured for SERIAL input/output."])
			l += [
				"serial=%s,%s%s%s" % (c["serial/unit"], c["serial/speed"], c["serial/parity"][0], c["serial/word"]),
			]
		# Global options need to come first
		l += [
				 timeout,
				 # Replace spaces with "_" in default name. Lilo doesn't like spaces
				 "default=\"{name}\"".format(name=self.defname.replace(" ", "_")),
			 ] + l
		
		return ok, l
