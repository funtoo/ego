#!/usr/bin/python3

from enum import Enum

class BootLoaderEntryType(Enum):
	LINUX = "linux"
	OTHER = "other"


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
		
		# we will look for these as we add boot entries:
		self.attempt_position = None
		self.attempt_kname = None
		self.attempt_success = None
		
		self.extension = extension

		if user_specified_attempt_identifier is not None:
			
			# user is telling us to attempt a particular kernel, falling back if it doesn't work.
			self.user_specified_attempt_identifier = user_specified_attempt_identifier
			try:
				pos = int(user_specified_attempt_identifier)
				if 0 <= pos:
					# identifier is an integer boot menu position:
					self.attempt_position = pos
					return
			except ValueError:
				pass
			# identifier is a path, it appears:
			self.attempt_kname = user_specified_attempt_identifier
			# Now, as we have menu entries added, we can look for matches.
		else:
			# See if we have a kernel already set to be promoted.
			self.attempt_kname = config.idmapper.get_attempted_kname()
	
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
			"image_path": image_path
		}
		self.boot_entries.append(entry)
		

