# -*- coding: ascii -*-

import os
import shlex
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

from funtoo.boot.extension import Extension
from funtoo.boot.extension import ExtensionError


def getExtension(config):
	""" Gets the extension based on the configuration """
	return GRUBExtension(config)


class GRUBExtension(Extension):
	""" Implements an extension for the grub bootloader """
	
	def __init__(self, config, testing=False):
		Extension.__init__(self, config)
		self.grubpath = "{path}/{dir}".format(path=self.config["boot/path"], dir=self.config["grub/dir"])
		self.fn = "{path}/{file}".format(path=self.grubpath, file=self.config["grub/file"])
		self.bootitems = []
		self.testing = testing
		self.GuppyMap()
		self.defpos = 0
		self.defname = "undefined"

		if os.path.exists("/sys/firmware/efi"):
			self.uefiboot = True
		else:
			self.uefiboot = False
	
	def grubProbe(self):
		gprobe = "/usr/sbin/grub-probe"
		if not os.path.exists(gprobe):
			gprobe = "/sbin/grub-probe"
		if not os.path.exists(gprobe):
			raise ExtensionError("couldn't find grub-probe")
		return gprobe
	
	def generateOtherBootEntry(self, l, sect):
		""" Generates the boot entry for other systems """
		ok = True
		mytype = self.config["{s}/type".format(s=sect)].lower()
		if mytype in ["dos", "msdos"]:
			mytype = "dos"
		elif mytype in ["windows", "windows 2000", "win2000", "windows xp", "winxp"]:
			mytype = "winxp"
		elif mytype in ["windows vista", "vista"]:
			mytype = "vista"
		elif mytype in ["windows 7", "win7"]:
			mytype = "win7"
		elif mytype in ["windows 8", "win8"]:
			mytype = "win8"
		elif mytype in ["windows 10", "win10"]:
			mytype = "win10"
		elif mytype in ["haiku", "haiku os"]:
			mytype = "haiku"
		elif mytype in ["linux16"]:
			mytype = "linux16"
		else:
			self.msgs.append(["fatal", "Unrecognized boot entry type \"{mt}\"".format(mt=mytype)])
			return False
		params = self.config["{s}/params".format(s=sect)].split()
		myroot = self.r.GetParam(params, "root=")
		mychainloader = self.r.GetParam(params, "chainloader=")
		myname = sect
		# TODO check for valid root entry
		l.append("")
		l.append("menuentry \"{mn}\" {{".format(mn=myname))
		if mytype in ["linux16"]:
			k = self.r.StripMountPoint(self.config[sect + "/kernel"])
			if not os.path.exists(self.config["boot/path"] + "/" + k):
				self.msgs.append(["warn", "Image for section {sect} not found - {k}".format(sect=sect, k=k)])
			else:
				self.bootitems.append(myname)
				l.append("  linux16 " + k)
		else:
			self.PrepareGRUBForDevice(myroot, l)
			self.bootitems.append(myname)
			self.DeviceGRUB(myroot)
			if mytype in ["win7", "win8"] or mytype == "win10" and self.uefiboot is False:
				l.append("  chainloader " + mychainloader) if mychainloader else l.append("  chainloader +4")
			elif mytype in ["vista", "dos", "winxp", "haiku"]:
				l.append("  chainloader " + mychainloader) if mychainloader else l.append("  chainloader +1")
			elif mytype in ["win10"]:
				l.append("  chainloader " + mychainloader) if mychainloader else l.append("  chainloader /EFI/Microsoft/Boot/bootmgfw.efi")
		l.append("}")
		return True
	
	def generateBootEntry(self, l, sect, k_full_path, kext):
		""" Generates the boot entry """
		ok = True
		mytype = self.config["{s}/type".format(s=sect)]
		l.append("")
		label = self.r.GetBootEntryString(sect, k_full_path)
		l.append("menuentry \"{l}\" {{".format(l=label))
		
		# self.bootitems records all our boot items
		self.bootitems.append(label)
		
		self.PrepareGRUBForFilesystem(self.config["{s}/scan".format(s=sect)], l)
		
		k_sub_path = self.r.StripMountPoint(k_full_path)
		c = self.config
		params = []
		if c.hasItem("boot/terminal") and c["boot/terminal"] == "serial":
			params += [
				"console=tty0",
				"console=ttyS%s,%s%s%s" % (c["serial/unit"], c["serial/speed"], c["serial/parity"][0], c["serial/word"])
			]
		params += self.config["{s}/params".format(s=sect)].split()
		
		ok, myroot = self.r.calculate_rootfs_for_section(params)
		if not ok:
			return False
		ok, fstype = self.r.calculate_rootfs_for_section(params)
		if not ok:
			return False
		
		initrds = self.config.item(sect, "initrd")
		initrds = self.r.FindInitrds(initrds, k_full_path, kext)
		if myroot and ('root=' + myroot) in params and 0 == len(initrds):
			params.remove('root=' + myroot)
			params.append('root=' + self.r.resolvedev(myroot))
		
		xenpath = None
		xenparams = None
		
		# Populate xen variables if type is xen
		if mytype == "xen":
			xenkernel = self.config["{s}/xenkernel".format(s=sect)]
			# Add leading / if needed
			if not xenkernel.startswith("/"):
				xenkernel = "/{xker}".format(xker=xenkernel)
			xenpath = self.r.StripMountPoint(xenkernel)
			xenparams = self.config["{s}/xenparams".format(s=sect)].split()
		
		# Add unique identifier that can be used to determine if kernel booted.
		params.append("rand_id=%s" % self.r.idmapper.get(k_full_path))
		# Append kernel lines based on type
		if mytype == "xen":
			l.append("  multiboot {xker} {xparams}".format(xker=xenpath, xparams=" ".join(xenparams)))
			l.append("  module {ker} {params}".format(ker=k_sub_path, params=" ".join(params)))
			for initrd in initrds:
				l.append("  module {initrd}".format(initrd=self.r.StripMountPoint(initrd)))
		else:
			l.append("  {t} {k} {par}".format(t=mytype, k=k_sub_path, par=" ".join(params)))
			if initrds:
				initrds = (self.r.StripMountPoint(initrd) for initrd in initrds)
				l.append("  initrd {rds}".format(rds=" ".join(initrds)))
		
		# Append graphics line
		if self.config.hasItem("{s}/gfxmode".format(s=sect)):
			skipgfx = False
			for p in params:
				if p.startswith("vga=") or p.startswith("video=uvesafb:"):
					skipgfx = True
					break
			if not skipgfx:
				l.append("  set gfxpayload=keep")
		l.append("}")
		
		return ok
	
	def sanitizeDisplayMode(self, dm):
		if self.uefiboot and dm == "text":
			# UEFI doesn't support text mode:
			return "640x480"
		else:
			return dm
	
	def generateConfigFile(self):
		l = []
		c = self.config
		if self.uefiboot:
			self.msgs.append(["note", "Detected UEFI boot. Configuring for UEFI booting."])
		else:
			self.msgs.append(["note", "Detected MBR boot. Configuring for Legacy MBR booting."])
		l.append(c.condFormatSubItem("boot/timeout", "set timeout={s}"))
		# pass our boot entry generator function to GenerateSections,
		# and everything is taken care of for our boot entries
		if c.hasItem("boot/terminal") and c["boot/terminal"] == "serial":
			self.msgs.append(["warn", "Configured for SERIAL input/output."])
			l += [
				"serial --unit=%s --speed=%s --word=%s --parity=%s --stop=%s" % (
				c["serial/unit"], c["serial/speed"], c["serial/word"], c["serial/parity"], c["serial/stop"]),
				"terminal_input serial",
				"terminal_output serial"
			]
		elif c.hasItem("display/gfxmode"):
			l.append("")
			self.PrepareGRUBForFilesystem(c["boot/path"], l)
			if c.hasItem("display/font"):
				font = c["display/font"]
			else:
				font = None
			
			dst_font = None
			
			if font is None:
				fonts = ["unicode.pf2", "unifont.pf2"]
			else:
				fonts = [font]
			
			for fontpath in [self.grubpath, self.grubpath + "/fonts"]:
				if dst_font is not None:
					break
				for font in fonts:
					path_to_font = fontpath + "/" + font
					if os.path.exists(path_to_font):
						dst_font = path_to_font
						break
			
			if dst_font is None:
				# font does not exist at destination... so we will need to find it somewhere and copy into /boot/grub
				for fontpath in c["grub/font_src"].split():
					if dst_font is not None:
						break
					for font in fonts:
						path_to_font = fontpath + "/" + font
						if os.path.exists(path_to_font):
							src_font = path_to_font
							dst_font = self.grubpath + '/fonts' + font
							if not os.path.exists(dst_font):
								import shutil
								shutil.copy(src_font, dst_font)
							break
			
			if dst_font is None:
				if font:
					self.msgs.append(["fatal", "specified font \"{ft}\" not found at {dst}; aborting.".format(ft=font, dst=dst_font)])
				else:
					self.msgs.append(["fatal", "Could not find one of %s to copy into boot directory; aborting." % ",".join(fonts)])
				return False, l
			
			l += ["if loadfont {dst}; then".format(dst=self.r.RelativePathTo(dst_font, c["boot/path"])),
				  "   set gfxmode={gfx}".format(gfx=self.sanitizeDisplayMode(c["display/gfxmode"])),
				  "   insmod all_video",
				  "   terminal_output gfxterm"]
			bg = c.item("display", "background").split()
			if len(bg):
				if len(bg) == 1:
					bgimg = bg[0]
					bgext = bg[0].rsplit(".")[-1].lower()
				elif len(bg) == 2:
					bgimg, bgext = bg
				if bgext == "jpg":
					bgext = "jpeg"
				if bgext in ["jpeg", "png", "tga"]:
					
					rel_cfgpath = "{path}/{img}".format(path=c["boot/path"], img=bgimg)
					
					# first, look for absolute path, because our relative path
					# can eval to "/boot/boot/foo.png" which
					# due to the /boot/boot symlink will "exist".
					
					if bgimg[0] == "/" and os.path.exists(bgimg):
						# user specified absolute path to file on disk:
						l += [
							"   insmod {bg}".format(bg=bgext),
							"   background_image {img}".format(img=self.r.RelativePathTo(bgimg, c["boot/path"]))
						]
					elif os.path.exists(rel_cfgpath):
						# user specified path relative to /boot:
						l += [
							"   insmod {ext}".format(ext=bgext),
							"   background_image {img}".format(img=self.r.RelativePathTo(rel_cfgpath, c["boot/path"]))
						]
					else:
						self.msgs.append(["warn", "background image \"{img}\" does not exist - skipping.".format(img=bgimg)])
				else:
					self.msgs.append(["warn", "background image \"{img}\" (format \"{ext}\") not recognized - skipping.".format(img=bgimg, ext=bgext)])
			l += ["fi",
				  "",
				  c.condFormatSubItem("color/normal", "set menu_color_normal={s}"),
				  c.condFormatSubItem("color/highlight", "set menu_color_highlight={s}"),
				  ]
		else:
			if c.hasItem("display/background"):
				self.msgs.append(["warn", "display/gfxmode not provided - display/background \"{bg}\" will not be displayed.".format(bg=c["display/background"])])
		
		ok, self.defpos, self.defname = self.r.GenerateSections(l, self.generateBootEntry, self.generateOtherBootEntry)
		if not ok:
			return ok, l
		
		l += [
			""
			"set default={pos}".format(pos=self.defpos)
		]
		
		return ok, l
	
	def GuppyMap(self):
		""" Creates the device map """
		gmkdevmap = "/sbin/grub-mkdevicemap"
		if not os.path.exists(gmkdevmap):
			# grub-2.00 and above does not have mkdevicemap - so skip it if we don't see it.
			return
		cmdobj = None
		if self.testing:
			cmdstr = "{gm} --no-floppy --device-map=/dev/null".format(gm=gmkdevmap)
			cmdobj = Popen(cmdstr, bufsize=-1, stdout=PIPE, stderr=STDOUT, shell=True)
		else:
			cmdobj = Popen([gmkdevmap, "--no-floppy"], bufsize=-1, stdout=PIPE, stderr=STDOUT, shell=False)
		output = cmdobj.communicate()
		if cmdobj.poll() != 0:
			raise ExtensionError("{cmd}\n{out}".format(cmd=gmkdevmap, out=output[0].decode()))
	
	def Guppy(self, argstring, fatal=True):
		""" Probes a device """
		gprobe = self.grubProbe()
		cmd = shlex.split("{gcmd} {args}".format(gcmd=gprobe, args=argstring))
		cmdobj = Popen(cmd, bufsize=-1, stdout=PIPE, stderr=PIPE, shell=False)
		output = cmdobj.communicate()
		retval = cmdobj.poll()
		if fatal and retval != 0:
			raise ExtensionError("{cmd} {args}\n{out}".format(cmd=gprobe, args=argstring, out=output[0].decode()))
		else:
			return retval, output[0].decode().strip("\n")
	
	def RequiredGRUBModules(self, dev):
		""" Determines required grub modules """
		mods = []
		for targ in ["abstraction", "partmap", "fs"]:
			for mod in self.DeviceProbe(dev, targ):
				# grub-1.98 will return "part_gpt", while 2.00 will return "gpt" -- accommodate this:
				if targ == "partmap" and mod[:5] != "part_":
					mod = "part_" + mod
				mods.append(mod)
		return mods
	
	def DeviceProbe(self, dev, targ):
		""" Determines the device details """
		retval, mods = self.Guppy(" --device {d} --target={t}".format(d=dev, t=targ))
		if retval == 0:
			return mods.split()
		else:
			return []
	
	def DeviceOfFilesystem(self, fs):
		""" Determines the device of a filesystem """
		retval, out = self.Guppy(" --target=device {f}".format(f=fs))
		return retval, out
	
	def DeviceUUID(self, dev):
		""" Determines the UUID of the filesystem """
		retval, out = self.Guppy(" --device {d} --target=fs_uuid".format(d=dev))
		return retval, out
	
	def DeviceGRUB(self, dev):
		""" Determines the Grub device for a Linux device """
		retval, out = self.Guppy(" --device {d} --target=drive".format(d=dev))
		return retval, out
	
	def PrepareGRUBForFilesystem(self, fs, l):
		""" Prepares Grub for the filesystem """
		retval, dev = self.DeviceOfFilesystem(fs)
		return self.PrepareGRUBForDevice(dev, l)
	
	def PrepareGRUBForDevice(self, dev, l):
		""" Prepares Grub for the device """
		for mod in self.RequiredGRUBModules(dev):
			l.append("  insmod {m}".format(m=mod))
		retval, grubdev = self.DeviceGRUB(dev)
		l.append("  set root={dev}".format(dev=grubdev))
		retval, uuid = self.DeviceUUID(dev)
		if retval == 0:
			l.append("  search --no-floppy --fs-uuid --set {u}".format(u=uuid))
	# TODO: add error handling for retvals

# vim: ts=4 sw=4 noet
