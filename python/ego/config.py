#!/usr/bin/python3

import sys
from configparser import InterpolationError
import os
import glob
import json
from collections import OrderedDict
from pathlib import Path

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
	def kit_info(self):
		return self.load_kit_metadata('info')

	@property
	def kit_sha1(self):
		return self.load_kit_metadata('sha1')

	def get_configured_kit(self, kit, show_default=False):
		if "kits" in self.settings and kit in self.settings["kits"]:
			branch = self.settings["kits"][kit]
		else:
			branch = None
		if branch and not show_default:
			return branch
		default = self.kit_info["kit_settings"][kit]["default"]
		if show_default:
			return (branch, default)
		else:
			return default

	def __init__(self, settings, settings_path, install_path="/usr/share/ego"):

		# TODO: This is a mess and needs some cleaning up

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

		self.meta_repo_root = self.get_setting("global", "meta_repo_path", "/var/git/meta-repo")
		self.sync_base_url = self.get_setting("global", "sync_base_url", "https://github.com/funtoo/{repo}")
		self.meta_repo_branch = self.get_setting("global", "meta_repo_branch", "master")
		self.repos_conf_path = self.get_setting("global", "repos_conf_path", "/etc/portage/repos.conf")

		kit_path = self.get_setting("global", "kits_path", "kits")
		if kit_path.startswith("/"):
			self.kit_root = kit_path
		else:
			self.kit_root = os.path.join(self.meta_repo_root, kit_path)
		self.sync_user = self.get_setting("global", "sync_user", "portage")

		self.kits_depth = self.get_setting("global", "kits_depth", 2)

	def available_modules(self):
		for x in self.ego_mods:
			yield x, self.ego_mods_info[x]
