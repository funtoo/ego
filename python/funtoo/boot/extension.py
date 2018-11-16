#!/usr/bin/python3

import os
from funtoo.boot.resolver import Resolver
from funtoo.boot.menu import BootLoaderMenu
from typing import Optional
from ego.output import mesg


class ExtensionError(Exception):
	def __init__(self, *args):
		self.args = args
		
	def __str__(self):
		if len(self.args) == 1:
			return str(self.args[0])
		else:
			return "(no message)"


class Extension:
	def __init__(self, boot_config, config, boot_options, ego_module):
		# initialization should always succeed.
		self.boot_config = boot_config
		self.config = config
		self.boot_options = boot_options
		self.ego_module = ego_module
		self.fn = None
		self.resolver = Resolver(boot_config, config, boot_options, ego_module)

	@property
	def msgs(self):
		return self.ego_module.msgs

	def attemptKernel(self, identifier) -> bool:
		self.msgs.append(["fatal", "This extension does not support kernel attempt/fallback."])
		return False

	def APIVersion(self) -> int:
		""" Returns API version, a monotonically increasing integer. """
		return 1

	def isAvailable(self) -> bool:
		""" Checks to ensure boot loader is available for use and all required local dependencies are satisfied. True = OK, False = not OK """
		return True

	def generateConfigFile(self, boot_menu: BootLoaderMenu):
		""" Generate new config file based on config data. Returns a list of all lines of the config file, without trailing newlines. """
		return BootLoaderMenu()

	def writeConfigFile(self, lines) -> bool:
		"""
		Create a new config file on disk - rather than call generateConfigFile() ourselves, we are passed the
		lines we want to print. This allows us to only generate them once, allowing validateConfigFile() to
		take a look at them first to print any warnings, etc.
		"""
		out = open(self.fn, "w")
		for line in lines:
			out.write(line+"\n")
		out.close()
		return True

	def backupConfigFile(self) -> bool:
		""" Create backup as necessary """
		oldfn = self.fn+".old"
		if os.path.exists(self.fn):
			if os.path.exists(oldfn):
				os.unlink(oldfn)
			os.rename(self.fn,oldfn)
		return True

	def validateConfigFile(self, lines: list) -> bool:
		"""
		This method should be overridden - it looks at the config file specified in the "lines" list, and
		prints any warnings or throws any errors as required.

		Return values:
			[ True, [list of warnings] ] - OK
			[ False, [list of warnings, errors] - Not OK, should abort.
		"""
		return True

	def updateBootLoader(self) -> bool:
		""" This method should be overridden. For LILO, run it to update the boot loader map. For grub, probably do nothing. """
		return True

	def regenerate(self, boot_menu: BootLoaderMenu) -> bool:
		""" This method performs the main loop that calls all our sub-steps - you should not need to override this method. If you do, an API upgrade is probably in order. """

		# CHECK DEPENDENCIES

		ok = self.isAvailable()
		if not ok:
			return False

		# TRY GENERATING CONFIG FILE - in memory, not yet written to disk

		self.generateConfigFile(boot_menu)
		if not boot_menu.success:
			return False

		self.msgs.append(["info", "Configuration file {name} generated - {num} lines.".format(name=self.fn, num=len(boot_menu.lines))])

		# TRY VALIDATING CONFIG FILE

		mesg("debug", "Validating config file {name}".format(name=self.fn))

		ok = self.validateConfigFile(boot_menu.lines)
		if not ok:
			return False

		# TRY BACKING UP CONFIG FILE

		mesg("debug", "Backing up original config file to {name}.old".format(name=self.fn))

		ok = self.backupConfigFile()
		if not ok:
			return False
			
		# TRY WRITING CONFIG FILE

		mesg("debug", "Writing new config file to {name}".format(name=self.fn))

		ok = self.writeConfigFile(boot_menu.lines)
		if not ok:
			return False

		# TRY UPDATING BOOT LOADER

		ok = self.updateBootLoader()
		if not ok:
			return False

		return True

# vim: ts=4 sw=4 noet
