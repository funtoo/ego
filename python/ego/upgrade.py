#!/usr/bin/python3

import os
from ego.config import getConfig
from ego.output import Output
import json

class UpgradeLister:

	"""

	UpgradeLister is used to list new to-be-applied upgrade files stored in /var/git/meta-repo/upgrades/YYYY/.

	The get_new_upgrades() method is a generator that returns a dict of info on each to-be-applied upgrade JSON.
	The set_last_upgrade() method is used to update /var/lib/ego/last-upgrade to the most recent upgrade applied.

	"""

	def __init__(self):

		self.config = getConfig()
		self.last_upgrade = None

		try:
			if not os.path.exists("/var/lib/ego"):
				os.makedirs("/var/lib/ego")
		except PermissionError:
			Output.fatal("Couldn't create /var/lib/ego. Ensure you have proper permissions.")
		try:
			if os.path.exists("/var/lib/ego/last-upgrade"):
				with open("/var/lib/ego/last-upgrade", "r") as myf:
					self.last_upgrade = myf.read().strip()
		except PermissionError:
			Output.fatal("Unable to read /var/lib/ego/last-upgrade. Please check permissions.")

	def set_last_upgrade(self, year, num):
		with open("/var/lib/ego/last-upgrade", "w") as myf:
			myf.write("%s/%s" % (year, num))

	def get_new_upgrades(self):

		if self.last_upgrade is not None:
			upgrade_year, upgrade_num = self.last_upgrade.split("/")
			upgrade_year = int(upgrade_year)
			upgrade_num = int(upgrade_num)
		else:
			upgrade_year = upgrade_num = 0

		#upgrade_dir = self.config.meta_repo_root + "/upgrades"
		upgrade_dir = "/var/src/meta-repo/upgrades"
		for cur_year_dir in sorted(list(os.listdir(upgrade_dir))):
			if not os.path.isdir(upgrade_dir + "/" + cur_year_dir):
				continue
			try:
				cur_year = int(cur_year_dir)
			except ValueError:
				continue
			if cur_year < upgrade_year:
				continue
			upgrade_path = upgrade_dir + "/" + cur_year_dir
			for cur_upgrade in os.listdir(upgrade_path):
				try:
					cur_upgrade_num = cur_upgrade.split("-")[0]
				except IndexError:
					continue
				try:
					cur_upgrade_num = int(cur_upgrade_num)
				except ValueError:
					continue
				if cur_year == upgrade_year and cur_upgrade_num < upgrade_num:
					continue
				elif cur_year < upgrade_year:
					continue
				yield {
					"path" : upgrade_path + "/" + cur_upgrade,
					"year" : cur_year,
					"number" : cur_upgrade_num
				}


class UpgradeHandler:

	"""

	UpgradeHandler is used to load an individual JSON upgrade file for processing.

	"""

	def __init__(self, path, year, number):
		self.path = path
		self.year = year
		self.number = number
		with open(self.path, "r", encoding="utf-8") as myf:
			self.json_data = json.loads(myf.read())

	@property
	def name(self):
		return self.json_data["name"]

	@property
	def steps(self):
		return self.json_data["steps"]


