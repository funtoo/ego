import os
from ego.output import Output


class ReleaseHandler:

	"""

	ReleaseHandler is used to load and set the current release version of Funtoo Linux.
	This information is stored in /var/lib/ego/release.
	If no release version is set, the release is None.

	set_release() is used to set the current release version.

	"""

	def __init__(self):

		self.release = None

		try:
			if not os.path.exists("/var/lib/ego"):
				os.makedirs("/var/lib/ego")
		except PermissionError:
			Output.fatal("Couldn't create /var/lib/ego. Ensure you have proper permissions.")
		try:
			if os.path.exists("/var/lib/ego/release"):
				with open("/var/lib/ego/release", "r") as myf:
					self.release = myf.read().strip()
		except PermissionError:
			Output.fatal("Unable to read /var/lib/ego/release. Please check permissions.")

	def set_release(self, release):
		with open("/var/lib/ego/release", "w") as myf:
			myf.write("%s/%s" % release)
