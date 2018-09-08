#!/usr/bin/python3

import sys

import os
import glob
import json
from collections import OrderedDict
from pathlib import Path
import configparser
from configparser import InterpolationError

def join_path(x, y):
	# ignore absolute paths (leading "/") in second component, for convenience...
	if y.startswith("/"):
		return os.path.join(x, y[1:])
	else:
		return os.path.join(x,y)

class EgoConfig(object):

	def get_setting(self, section, key, default=None):
		if section in self.settings and key in self.settings[section]:
			try:
				return self.settings[section][key]
			except InterpolationError:
				sys.stderr.write(
					"There is an error in your ego.conf at section '%s', key '%s'.\n" % (section, key)
				)
				sys.exit(1)
		else:
			return default

	def set_setting(self, section, key, value):
		if section not in self.settings:
			self.settings.add_section(section)
		self.settings.set(section, key, value)
		self._save()

	def _save(self):
		with open(self.settings_path, "w") as outfile:
			self.settings.write(outfile)

	def metadata_exists(self):
		if os.path.exists(self.meta_repo_root) and os.path.exists(self.meta_repo_root + "/metadata"):
			return True
		else:
			return False

	def load_kit_metadata(self, fn):
		if not hasattr(self, '_kit_%s' % fn):
			path = Path(self.meta_repo_root) / 'metadata' / ('kit-%s.json' % fn)
			try:
				with path.open() as f:
					return json.loads(f.read(), object_pairs_hook=OrderedDict)
			except OSError:
				return {}
		return getattr(self, '_kit_%s' % fn)

	@property
	def kit_info_metadata(self):
		return self.load_kit_metadata('info')

	@property
	def kit_sha1_metadata(self):
		return self.load_kit_metadata('sha1')

	@property
	def default_release(self):
		try:
			return self.kit_info_metadata["release_info"]["default"]
		except KeyError:
			return None

	@property
	def release(self):
		try:
			return self.settings["global"]["release"]
		except KeyError:
			return self.default_release

	def get_kit_version_of_release(self, release, kit):
		try:
			return self.kit_info_metadata["release_defs"]["%s-release" % release][kit][0]
		except KeyError:
			return None

	def kit_branch_is_deprecated(self, kit, branch):
		try:
			return self.kit_info_metadata["kit_settings"][kit]["stability"][branch] == "deprecated"
		except KeyError:
			return True
		return True

	def kit_branch_stability(self, kit, branch):
		try:
			return self.kit_info_metadata["kit_settings"][kit]["stability"][branch]
		except KeyError:
			pass
		return "deprecated"

	def get_configured_kit(self, kit):
		if "kits" in self.settings and kit in self.settings["kits"]:
			kit_branch = self.settings["kits"][kit]
		else:
			kit_branch = None

		release = self.release

		default_kit_branch = None
		try:
			if release is not None:
				default_kit_branch = self.get_kit_version_of_release(self.release, kit)
			if default_kit_branch is None:
				default_kit_branch = self.kit_info_metadata["kit_settings"][kit]["default"]
			if kit_branch is None:
				kit_branch = default_kit_branch
		except KeyError:
			pass
		return kit_branch, default_kit_branch


	def __init__(self, settings, settings_path, root_path="/", install_path="/usr/share/ego"):

		# TODO: This is a mess and needs some cleaning up

		self.root_path = root_path
		self.ego_dir = install_path
		self.ego_mods_dir = "%s/modules" % self.ego_dir
		self.ego_mods_info_dir = "%s/modules-info" % self.ego_dir
		self.ego_mods = []
		self.ego_mods_info = {}

		if os.path.isdir(self.ego_mods_dir):
			for match in glob.glob(self.ego_mods_dir + "/*.ego"):
				self.ego_mods.append(match.split("/")[-1][:-4])
		for mod in self.ego_mods:
			inf_path = self.ego_mods_info_dir + "/" + mod + ".json"
			if os.path.exists(inf_path):
				with open(inf_path, "r") as inf:
					self.ego_mods_info[mod] = json.loads(inf.read())
			else:
				self.ego_mods_info[mod] = {}
		self.settings = settings
		self.settings_path = settings_path

		self.meta_repo_root = self.get_setting("global", "meta_repo_path", join_path(self.root_path, "/var/git/meta-repo"))
		self.sync_base_url = self.get_setting("global", "sync_base_url", "https://github.com/funtoo/{repo}")
		self.meta_repo_branch = self.get_setting("global", "meta_repo_branch", "master")
		self.repos_conf_path = self.get_setting("global", "repos_conf_path", join_path(self.root_path, "/etc/portage/repos.conf"))

		kit_path = self.get_setting("global", "kits_path", "kits")
		if kit_path.startswith("/"):
			self.kits_root = join_path(self.root_path, kit_path)
		else:
			self.kits_root = os.path.join(self.meta_repo_root, kit_path)
		r_common = os.path.commonprefix([self.root_path, self.kits_root])
		self.unprefixed_kits_root = self.kits_root[len(r_common):]
		if not self.unprefixed_kits_root.startswith("/"):
			self.unprefixed_kits_root = "/" + self.unprefixed_kits_root
		self.sync_user = self.get_setting("global", "sync_user", "portage")

		self.kits_depth = self.get_setting("global", "kits_depth", 2)

	def available_modules(self):
		for x in self.ego_mods:
			yield x, self.ego_mods_info[x]
