#!/usr/bin/python3

import os
import random
import string

from funtoo.core import config

class KernelIDMapper:
	"""Kernel ID mapper to generate unique random IDs for specific kernel images, so they can be identified via a rand_id boot parameter."""
	
	# mapping from rand_id to kernel image name:
	file_path = "/etc/boot.d/config/kernel/random.map"
	
	# record of last kernel booted:
	last_path = "/etc/boot.d/config/kernel/last_id"
	
	# rand_id of kernel to promote to default, if booted:
	promote_path = "/etc/boot.d/config/kernel/promote_id"
	
	# id of default kernel to boot (overrides config file):
	default_path = "/etc/boot.d/config/kernel/default_id"
	
	@classmethod
	def get_active_rand_id(cls):
		"""Returns rand_id of kernel that is currently running, or None if not set."""
		with open("/proc/cmdline", "r") as f:
			params = f.read().split()
			for param in params:
				if param.startswith("rand_id="):
					return param[8:]
		return None
	
	@classmethod
	def record_rand_id_to_file(cls, rand_id, file_path):
		"""Record rand_id to a file (could be last_path, promote_path, default_path)"""
		dirpath = os.path.dirname(file_path)
		if not os.path.exists(dirpath):
			os.makedirs(dirpath)
		with open(file_path, "w") as f:
			f.write(rand_id)
	
	def __init__(self):
		self.rand_to_kernel_map = {}
		self.kernel_to_rand_map = {}
		self.load_mappings(self.file_path)
	
	def update_last_id(self):
		"""Update the id of the last booted kernel -- used after a successful boot."""
		current_id = self.get_active_rand_id()
		if current_id is not None:
			self.record_rand_id_to_file(current_id, self.last_path)
	
	def update_promote_kname(self, promote_kname):
		"""Set an id to promote on next successful boot. In other words, set the special file that tells us that we are attempting a particular kernel."""
		rand_id = self.get(promote_kname)
		self.record_rand_id_to_file(rand_id, self.promote_path)
		
	def remove_promote_setting(self):
		if os.path.exists(self.promote_path):
			os.unlink(self.promote_path)
	
	def promote_kernel(self) -> (bool, str):
		"""If a rand_id is in the promote file, this method tells us to set it as the default. Used for fallback."""
		promote_id = self.load_promote_rand_id()
		if promote_id is not None:
			if promote_id == self.get_active_rand_id():
				# we've booted the to-be-promoted kernel -- let's make it default:
				self.record_rand_id_to_file(promote_id, self.default_path)
				return True, self.get_kname_of_rand_id(promote_id)
		if os.path.exists(self.promote_path):
			# Whether promoting or not, we want to remove the promote_id:
			os.unlink(self.promote_path)
		return False, None
	
	def get_kname_of_rand_id(self, rand_id) -> str:
		return self.rand_to_kernel_map[rand_id]
	
	def load_last_successful_rand_id(self) -> str:
		"""Get the rand_id of the last successful boot, if any."""
		return self.load_id_file(self.last_path)
	
	def load_default_rand_id(self) -> str:
		return self.load_id_file(self.default_path)
	
	def load_promote_rand_id(self) -> str:
		return self.load_id_file(self.promote_path)
	
	def get_attempted_kname(self) -> object:
		"""Return None if no default set in attempted path, else the default kname."""
		attempt_rand_id = self.load_promote_rand_id()
		if attempt_rand_id is None:
			return None
		if attempt_rand_id in self.rand_to_kernel_map.keys():
			return self.rand_to_kernel_map[attempt_rand_id]
		else:
			return None
	
	def get_default_kname(self) -> object:
		"""Return None if no default set in default_path, else the default kname."""
		default_rand_id = self.load_default_rand_id()
		if default_rand_id is None:
			return None
		if default_rand_id in self.rand_to_kernel_map.keys():
			return self.rand_to_kernel_map[default_rand_id]
		else:
			return None
	
	def set_default_kname(self, kname) -> bool:
		"""Set the default to-be-booted kernel by kname."""
		if kname not in self.kernel_to_rand_map:
			return False
		self.record_rand_id_to_file(self.kernel_to_rand_map[kname], self.default_path)
		return True
		
	def get_last_booted_kname(self) -> object:
		"""Return kname of last-booted kernel"""
		last_id = self.load_last_successful_rand_id()
		if last_id is None:
			return None
		if last_id in self.rand_to_kernel_map:
			return self.rand_to_kernel_map[last_id]
		else:
			return None
		
	def load_id_file(self, file_path):
		"""Load an id from disk"""
		if not os.path.exists(file_path):
			return None
		with open(file_path, "r") as f:
			return f.read().strip()
	
	def load_mappings(self, file_path):
		"""Load mappings from disk"""
		if not os.path.exists(self.file_path):
			return
		with open(file_path, "r") as f:
			for line in f.readlines():
				line = line.strip().split(":")
				if len(line) == 2:
					self.rand_to_kernel_map[line[0]] = line[1]
					self.kernel_to_rand_map[line[1]] = line[0]
	
	def get(self, kernel_name):
		"""Get a rand_id for a kernel, creating one if necessary."""
		if kernel_name in self.kernel_to_rand_map.keys():
			return self.kernel_to_rand_map[kernel_name]
		else:
			return self.add(kernel_name)
	
	def add(self, kernel_name):
		"""Add a rand_id/kernel_image mapping, and save to disk."""
		if kernel_name in self.kernel_to_rand_map.keys():
			return
		rand_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
		self.rand_to_kernel_map[rand_id] = kernel_name
		self.kernel_to_rand_map[kernel_name] = rand_id
		self.save()
		return rand_id
	
	def save(self):
		"""Save mappings to disk"""
		dirpath = os.path.dirname(self.file_path)
		if not os.path.exists(dirpath):
			os.makedirs(dirpath)
		with open(self.file_path, "w") as f:
			for rand_id, image_name in self.rand_to_kernel_map.items():
				f.write("%s:%s\n" % (rand_id, image_name))


class DefaultBootConfigFile(config.ConfigFile):
	
	def inherit(self, section):
		if section not in self.builtins:
			return "default"
		return None
	
	def __init__(self, fn="/etc/boot.conf.defaults", existing=True):
		self.builtins = ["boot", "default", "color", "grub", "grub-legacy", "lilo"]
		config.ConfigFile.__init__(self, fn, existing)


class BootConfigFile(config.ConfigFile):
	
	def inherit(self, section):
		if section not in self.builtins:
			return "default"
		return None
	
	def __init__(self, fn, existing=True, msgs=None):
		# builtins is our list of all those sections that we recognize as having config values and
		# not boot entries.
		self.builtins = ["boot", "display", "default", "altboot", "color", "grub", "grub-legacy", "lilo"]
		config.ConfigFile.__init__(self, fn, existing, msgs=msgs)
		self.parent = DefaultBootConfigFile()
		self.idmapper = KernelIDMapper()
	
	def get_default_boot_setting(self):
		"""This logic is becoming fairly complex so breaking it out into its own function. What is our default kernel or section?"""
		
		autopick_setting = self.item("boot", "autopick")
		default_in_boot_conf = self.item("boot", "default", bool=True)
		default_in_boot_d = self.idmapper.get_default_kname()
		last_booted = self.idmapper.get_last_booted_kname()
		
		if default_in_boot_d:
			return default_in_boot_d, "boot.d"
		elif default_in_boot_conf:
			return self.deburr(self.item("boot", "default")), "boot.conf"
		elif autopick_setting == "last-booted" and last_booted is not None:
			return self.idmapper.get_last_booted_kname(), "autopick: last-booted"
		else:
			return None, "autopick: mtime"
		
		# TODO: add last-selected, which is different from last-booted.
	
	def validate(self):
		invalid = []
		validmap = {
			"boot": ["path", "generate", "timeout", "default", "bootdev", "terminal", "autopick"],
			"display": ["gfxmode", "background", "font"],
			"color": ["normal", "highlight"],
			"default": ["scan", "gfxmode", "kernel", "initrd", "params", "type", "xenkernel", "xenparams", "attemptparams"],
			"grub": ["dir", "file", "grub-mkdevicemap", "grub-probe", "font_src"],
			"grub-legacy": ["dir", "file"],
			"lilo": ["file", "bin", "gparams"],
			"serial": ["parity", "port", "speed", "stop", "unit", "word"]
		}
		for section in self.sectionData.keys():
			if section not in validmap.keys():
				cmpto = "default"
			else:
				cmpto = section
			for itemkey in self.sectionData[section].keys():
				if itemkey not in validmap[cmpto]:
					invalid.append("{sect}/{name}".format(sect=section, name=itemkey))
		return invalid

# vim: ts=4 sw=4 noet
