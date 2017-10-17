#!/usr/bin/python3

"""

Here's what's going on. I'm rewriting profile.ego but in a way that is independent of ego, so it can be used as a
general API for handling profiles. I am also trying to make this code production-quality -- this includes making it
very clean, easy-to-understand, well-documented with concepts clearly explained, and easy to unit-test.


"""

import json
import os
from enum import Enum
import errno
from collections import OrderedDict

class ProfileType(Enum):
	ARCH = "arch"
	BUILD = "build"
	SUBARCH = "subarch"
	FLAVOR = "flavor"
	MIX_IN = "mix-ins"

class ProfileCatalog:

	"""

	``ProfileCatalog`` will allow us to see what profile settings -- flavors, subarches, mix-ins, builds -- are
	available in a particular profile repository.
	
	It is initialized by specifying a repository directory where ``ProfileCatalog`` will find an ``ego.desc`` file. This
	JSON file will be read in and contains paths where ProfileCatalog can find each type of sub-profile.
	
	ProfileCatalog allows an ``arch`` string to be set via ``self.set_arch()`` or specified directly as a keyword
	argument to the ``self.list() method. When specified, this string will be used to augment the list of mix-ins with
	subarch mix-ins, and provide a list of subarches. Note that without specifying ``arch``, it is impossible for
	``ProfileCatalog`` to know where to look for subarch profiles.
	
	"""

	def __init__(self, profile_root):
		self.profile_root = profile_root
		self.egodescfile = self.profile_root + "/profiles.ego.desc"

		self.json_info = {}
		if os.path.exists(self.egodescfile):
			with open(self.egodescfile, "r") as ed:
				self.json_info = json.loads(ed.read())
		for k in self.json_info:
			if not isinstance(self.json_info[k], list):
				# move everything inside a list if it isn't.
				self.json_info[k] = [self.json_info[k]]
		for pt in [ ProfileType.MIX_IN, ProfileType.SUBARCH ]:
			if pt not in self.json_info:
				self.json_info[pt] = []
		self.arch = None
		
	# keys() returns a list of types of sub-profiles that are defined on this system.

	def set_arch(self, arch=None):
		"Allows the arch to be set once, rather than passed as an argument to self.list."
		self.arch = arch

	def __getitem__(self, key, arch=None):
		return self.list(key, arch)

	def list(self, key, arch=None):
		
		"""
		Yields available profiles of a particular ProfileType.

		:param key: A string specifying the ProfileType to list.
		:param arch: An arch must be specified in order to also list ``subarch`` and arch-specific mix-ins.
		:return: generator
		"""

		if not arch and self.arch:
			arch = self.arch

		dirlist = [] # directories relative to self.repodir we will scan in phase 2 for list of this profile type

		if arch is not None:
			if key == ProfileType.SUBARCH:
				dirlist = [ self.json_info[ProfileType.ARCH] + "/" + arch + "/subarch" ]
			elif key == ProfileType.MIX_IN:
				dirlist = [ self.json_info[ProfileType.MIX_IN] + "/" + arch + "/mix-ins" ]

		if key in self.json_info:
			dirlist += self.json_info[key]

		for dir in dirlist:
			p = self.profile_root + "/" + dir
			try:
				for profile_root in os.listdir(p):
					if os.path.isdir(p + "/" + profile_root):
						yield profile_root
			except OSError as e:
				if e.errno not in (errno.ENOTDIR, errno.ENOENT, errno.ESTALE):
					raise
				continue

class ProfileSpecifier(object):

	""" ``ProfileSpecifier`` is an object used by ``ProfileTree`` to model the profile hierarchy. Each
	``ProfileSpecifier`` takes a specifier that is in one of the following formats::

	``:foo/bar/oni``
	  Relative to the base of the profile root.

	``foo:bar/oni``
	  Relative to the base of a particular repository.

	``[relative_path]``
	  A relative path specification that is interpreted relative to the current directory.

	"""

	def __init__(self, tree, cwd, specifier):
		"""
		:param tree: A ``ProfileTree`` object.
		:param cwd:  The current working directory of the ``parent`` file that the specifier came from.
		:param specifier: A single line from a ``parent`` file specifying another profile.
		"""

		self.tree = tree
		self.cwd = cwd
		self.specifier = specifier
		self._resolved_path = None

	def __str__(self):
		return self.specifier

	def __repr__(self):
		return "<ProfileSpecifier: %s>" % self.specifier

	@property
	def resolved_path(self):

		if self._resolved_path is None:

			if self.specifier[0] == ":":
				# ":base" format -- relative to root of profile directory:
				self._resolved_path = os.path.join(self.tree.catalog.profile_root, self.specifier[1:])
			else:
				colsplit = self.specifier.split(":")
				if len(colsplit) == 2 and colsplit[0] in self.tree.repomap:
					# "gentoo:foo" format - relative to a specified repo:
					self._resolved_path = os.path.join(self.tree.repomap[colsplit[0]], colsplit[1])
				else:
					if self.specifier.startswith("/"):
						# absolute path
						self._resolved_path = self.specifier
					else:
						# relative path format - relative to current location.
						self._resolved_path = os.path.join(self.cwd, self.specifier)

			self._resolved_path = os.path.normpath(self._resolved_path)

		return self._resolved_path

	def classify(self):

		"""
		This method will look at the resolved path and inspect it to see if it's a mix-in path, etc. We need this
		because the specifier doesn't tell us what type of profile it is, but that information is important to us.

		The way to tell is to look at the containing path and see if it is in a "flavor", etc. directory.

		:return: A ProfileType Enum telling us the type of profile, or None if not recognized as any particular kind.

		"""
		try:
			kind = self.resolved_path.split("/")[-2:-1][0]
			if kind in ProfileType.__members__:
				return ProfileType.__members__[kind]
		except IndexError:
			pass
		return None

class ProfileTree(object):

	"""
	The ```ProfileTree`` has the ability to look at the master profile settings, as well as the repositories, and
	process the inheritance patterns defined in ``parent`` files. This allows ``ProfileTree`` to determine what
	profiles are enabled, either directly or via inheritance. ``ProfileTree`` also provides a mechanism to write out
	new, modified master profile data in the proper format.

	The 'tree' of the ``ProfileTree`` begins with a root, which for Funtoo is going to be
	``/etc/portage/make.profile/parents``. This parents file will point to other profiles, which we will consider
	children. These child profiles may have their own children, etc. This hierarchy defines what profiles are enabled,
	and also defines the order in which various profile settings are interpreted.

	The profile hierarchy is stored in ``self.profile_heir``. It is generated as follows. The contents of
	``/etc/portage/make.profile/parents`` is parsed, and each literal profile specifier line is wrapped in a
	``ProfileSpecifier`` object. These lines become keys of the ordered dictionary, and their associated values are each
	a single ``OrderedDict`` containing lines (again, as ``ProfileSpecifiers``) of the ``parent`` file referenced by the
	original ``ProfileSpecifier`` key.
	"""

	def __init__(self, catalog, master_repo_name, repomap):

		self.catalog = catalog
		self.master_repo_name = master_repo_name
		self.repomap = repomap
		self.root_parent_dir = '/etc/portage/make.profile'
		self.profile_path_map = {}

		# profile_path_map: Map the absolute path of profile directory to an OrderedDict containing ProfileSpecifiers
		# for each line in the parent file of the directory it references.

		self.profile_hier = self._recurse()

	def _recurse(self, parent=None, profile_path=None):

		res_path = profile_path.resolved_path if profile_path is not None else self.root_parent_dir

		if res_path in self.profile_path_map:
			# we've already scanned this profile. Nice side-effect of preventing infinite loops.
			return self.profile_path_map[res_path]

		new_children = OrderedDict()
		for specifier in self._read_parent(res_path):
			spec_obj = ProfileSpecifier(self, res_path, specifier)
			new_children[spec_obj] = self._recurse(new_children, spec_obj)
		self.profile_path_map[res_path] = new_children
		return new_children

	def _read_parent(self, parent_dir):
		fn = os.path.join(parent_dir, "parent")
		if not os.path.exists(fn):
			raise StopIteration
		with open(fn, 'r') as f:
			for line in f.readlines():
				if len(line) and line[0] == "#":
					continue
				yield line.strip()

	def spiff(self):
		"A quick example that will output the contents of /etc/portage/make.profile/parent"
		for spec in self.profile_hier:
			print(repr(spec))
			print(str(spec))

if __name__ == "__main__":

	# A quick example to parse profiles in core-kit. Note how the profiles tree specified in the ProfileCatalog()
	# constructor is completely decoupled from the core-kit repo. In theory, it could live anywhere.

	pt = ProfileTree(ProfileCatalog("/var/git/meta-repo/kits/core-kit/profiles"), "core-kit", { "core-kit" : "/var/git/meta-repo/kits/core-kit"})
	pt.spiff()

# vim: ts=4 noet sw=4
