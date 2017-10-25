#!/usr/bin/python3

import sys
import configparser
from configparser import InterpolationError
import os
import json
import glob

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

	def __init__(self, install_path="/usr/share/ego"):

		settings = configparser.ConfigParser()
		try:
			settings.read('/etc/ego.conf')
		except IOError:
			print("Config file /etc/ego.conf not found.")
			sys.exit(1)

		if 'EGO_INSTALL_PATH' in os.environ:
			install_path = os.environ['EGO_INSTALL_PATH']
		elif "global" in settings and "install_path" in settings["global"]:
			install_path = settings["global"]["install_path"]

		sys.path.insert(0, install_path + "/python")

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

		self.meta_repo_root = self.get_setting("global", "meta_repo_path", "/var/git/meta-repo")
		self.sync_base_url = self.get_setting("global", "sync_base_url", "https://github.com/funtoo/{repo}")
		self.meta_repo_branch = self.get_setting("global", "meta_repo_branch", "master")
		kit_path = self.get_setting("global", "kits_path", "kits")
		if kit_path.startswith("/"):
			self.kit_root = kit_path
		else:
			self.kit_root = os.path.join(self.meta_repo_root, kit_path)
		self.sync_user = self.get_setting("global", "sync_user", "portage")

	def available_modules(self):
		for x in self.ego_mods:
			yield x, self.ego_mods_info[x]
