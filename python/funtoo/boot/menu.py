#!/usr/bin/python3

from enum import Enum
from ego.output import mesg

class BootLoaderEntryType(Enum):
	LINUX = "linux"
	OTHER = "other"

class BootMenuFlag(Enum):
	DEFAULT = "default"
	ATTEMPT = "attempt"

class BootLoaderMenu:
	"""
	A nicer way to record the contents ot the boot menu for later introspection.
	"""
	
	def __init__(self, extension, config, user_specified_attempt_identifier=None):
		self.boot_entries = []
		self.lines = []
		self.success = True
		self.default_position = None
		self.user_specified_attempt_identifier = user_specified_attempt_identifier
		self.config = config
		
		# we will look for these as we add boot entries:
		self._attempt_position = None
		self._attempt_kname = None

		# Set to true means: an attempted boot entry has been specified and found.
		# Used when adding boot entries to know if we should keep looking for a boot entry to attempt.
		self.attempt_tagged = False
		
		self.extension = extension

		if user_specified_attempt_identifier is not None:
			
			# user is telling us to attempt a particular kernel, falling back if it doesn't work.
			self.user_specified_attempt_identifier = user_specified_attempt_identifier
			try:
				pos = int(user_specified_attempt_identifier)
				if 0 <= pos:
					# identifier is an integer boot menu position:
					self._attempt_position = pos
					return
			except ValueError:
				pass
			# identifier is a path, it appears:
			self._attempt_kname = user_specified_attempt_identifier
			# Now, as we have menu entries added, we can look for matches.
		else:
			# See if we have a kernel already set to be promoted.
			self._attempt_kname = config.idmapper.get_attempted_kname()

	# self.attempt_position,
	# self.attempt_kname:
	#
	# We also want to make sure that self.attempt_kname *and* self.attempt_position have valid values.
	# The user is only going to specify either the kernel name or the position, so it's our job to
	# determine the correct value for the "other" variable automatically, based on the contents of
	# the boot menu.

	@property
	def attempt_position(self):
		if self._attempt_position is not None:
			return self._attempt_position
		elif self._attempt_kname is not None:
			for pos in range(0, len(self.boot_entries)):
				if "image_path" in self.boot_entries[pos]:
					if self.boot_entries[pos]["image_path"] == self._attempt_kname:
						return pos

	@property
	def attempt_kname(self):
		if self._attempt_kname is not None:
			return self._attempt_kname
		elif self._attempt_position is not None:
			if self._attempt_position < len(self.boot_entries):
				if "image_path" in self.boot_entries[self._attempt_position]:
					return self.boot_entries[self._attempt_position]["image_path"]


	def nextEntryPosition(self):
		return len(self.lines)
	
	def has_kname(self, kname):
		for item in self.boot_entries:
			if "image_path" in item and item["image_path"] == kname:
				return True
		return False
		
	def addBootEntry(self, boot_type: BootLoaderEntryType, label: str, image_path: str = None):
		entry = {
			"type": boot_type,
			"label": label,
			"image_path": image_path,
			"flags": [],
			"pos": len(self.boot_entries)
		}
		self.boot_entries.append(entry)

		# Set ATTEMPT flag as appropriate:
		if not self.attempt_tagged:
			pos = self.attempt_position
			if pos is not None:
				pos += 1
			if self.attempt_kname == image_path and pos != None and pos == len(self.boot_entries):
				entry["flags"].append(BootMenuFlag.ATTEMPT)
				self.attempt_tagged = True

		return entry

	def show(self):
		pos = 0
		found_default = False
		for item in self.boot_entries:
			if BootMenuFlag.DEFAULT in item["flags"]:
				found_default = True
				break
		for item in self.boot_entries:
			label = item["label"]
			if BootMenuFlag.ATTEMPT in item["flags"]:
				mesg("attemptboot", label, entry=pos)
			elif BootMenuFlag.DEFAULT in item["flags"] or (not found_default and pos == 0):
				mesg("defboot", label, entry=pos)
			else:
				mesg("boot", label, entry=pos)
			pos += 1
		

