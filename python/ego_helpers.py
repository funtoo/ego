#!/usr/bin/python3

import os
import json
import glob
import importlib.machinery
import sys

# Ego Helpers module.
#
# Copyright 2017 Daniel Robbins and Funtoo Solutions, Inc.
# See LICENSE.txt for terms of distribution. 

def get_install_path(settings):
	if "global" in settings and "install_path" in settings["global"]:
		return settings["global"]["install_path"]
	else:
		return "/usr/share/ego"

def get_ego_module(install_path, modname):
	loader = importlib.machinery.SourceFileLoader(modname, '%s/modules/%s.ego' % (install_path, modname))
	try:
		return loader.load_module()
	except FileNotFoundError:
		return None

def run_ego_module(install_path, modname, config, args):
	mod = get_ego_module(install_path, modname)
	if mod:
		ego_module = mod.Module(modname, install_path, config)
		ego_module(*args)
	else:
		print(Color.RED + "Error: ego module \"%s\" not found." % modname + Color.END)
		sys.exit(1)


class EgoConfig:

	def __init__(self, root, settings, version):

		# TODO: I'd like to add a verbosity level that can be defined in ego.conf or specified on the command-line.

		self.ego_version = version
		self.ego_dir = root
		self.ego_mods_dir = "%s/modules" % self.ego_dir
		self.ego_mods_info_dir = "%s/modules-info" % self.ego_dir
		self.ego_mods = []
		self.ego_mods_info = {}
		self.sync_base_url = "https://github.com/funtoo/%s"
		self.meta_repo_branch = "master"
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

		self.meta_repo_root = "/var/git/meta-repo"
		if "global" in self.settings and "meta_repo_path" in self.settings["global"]:
			self.meta_repo_root = self.settings["global"]["meta_repo_path"]

		if "global" in self.settings and "sync_base_url" in self.settings["global"]:
			self.sync_base_url = self.settings["global"]["sync_base_url"]
		if "global" in self.settings and "meta_repo_branch" in self.settings["global"]:
			self.meta_repo_branch = self.settings["global"]["meta_repo_branch"]
		kit_path = "kits"
		if "global" in self.settings and "kits_path" in self.settings["global"]:
			kit_path = self.settings["global"]["kits_path"]
		if kit_path.startswith("/"):
			self.kit_root = kit_path
		else:
			self.kit_root = os.path.join(self.meta_repo_root, kit_path)

		if "global" in self.settings and "sync_user" in self.settings["global"]:
			self.sync_user = self.settings["global"]["sync_user"]
		else:
			self.sync_user = "portage"

	def available_modules(self):
		for x in self.ego_mods:
			yield x, self.ego_mods_info[x]

class ColorType(str):
	pass

class Color(object):
	PURPLE = ColorType('\033[95m')
	CYAN = ColorType('\033[96m')
	DARKCYAN = ColorType('\033[36m')
	DARKBLUEBG = ColorType('\033[48;5;018m')
	BLUE = ColorType('\033[94m')
	GREEN = ColorType('\033[92m')
	YELLOW = ColorType('\033[93m')
	RED = ColorType('\033[91m')
	BOLD = ColorType('\033[1m')
	UNDERLINE = ColorType('\033[4m')
	END = ColorType('\033[0m')
	AUTOFLUSH = ColorType("")

	@classmethod
	def purple(cls, text):
		return cls((cls.PURPLE, text))

	@classmethod
	def cyan(cls, text):
		return cls((cls.CYAN, text))

	@classmethod
	def darkcyan(cls, text):
		return cls((cls.DARKCYAN, text))

	@classmethod
	def blue(cls, text):
		return cls((cls.BLUE, text))

	@classmethod
	def green(cls, text):
		return cls((cls.GREEN, text))

	@classmethod
	def yellow(cls, text):
		return cls((cls.YELLOW, text))

	@classmethod
	def red(cls, text):
		return cls((cls.RED, text))

	@classmethod
	def bold(cls, text):
		return cls((cls.BOLD, text))

	@classmethod
	def underline(cls, text):
		return cls((cls.UNDERLINE, text))

	@classmethod
	def default(cls, text):
		return cls((cls.END, text))

	def __init__(self, *chunks):
		self.chunks = chunks

	def __str__(self):
		return ''.join([x[0] + str(x[1]) + self.END for x in self.chunks])

	def __len__(self):
		return sum([len(x[1]) for x in self.chunks])

	def __add__(self, text):
		if not isinstance(text, self.__class__):
			text = self.__class__((self.END, text))
		chunks = self.chunks + text.chunks
		return self.__class__(*chunks)

	def rjust(self, width, fillchar=' '):
		return self.default(' ' * (width - len(self))) + self

	def ljust(self, width, fillchar=' '):
		return self + self.default(' ' * (width - len(self)))

def header(info):
	print("\n=== " + Color.BOLD + Color.GREEN + info + Color.END + ": ===\n")

class Table:

	def __init__(self, nb_columns, *, align='', col_sep=' ', row_sep='', lpad=0, rpad=0, join=None):
		self.align = align
		self.col_sep = col_sep
		self.row_sep = row_sep
		self.lpad = lpad
		self.rpad = rpad
		self.join = join or row_sep
		self.rows = []
		self.cols_width = (1,) * nb_columns

	def append(self, *cells):
		if self.lpad or self.rpad:
			cells = tuple(
				Color.default(' ' * self.lpad) + c + (' ' * self.rpad)
				for c in cells
			)
		self.cols_width = [
			max(self.cols_width[i], len(x)) for i, x in enumerate(cells)
		]
		self.rows.append(cells)

	def separator(self, separator=None):
		self.rows.append(separator or self.row_sep)

	def __str__(self):
		output = ''
		for row in self.rows:
			if not row:
				output += '\n'
			elif isinstance(row, tuple):
				cells = []
				for i, cell in enumerate(row):
					try:
						align = self.align[i]
					except IndexError:
						align = 'l'
					if align == 'l':
						cells.append(cell.ljust(self.cols_width[i]))
					elif align == 'r':
						cells.append(cell.rjust(self.cols_width[i]))
					elif align == 'c':
						cells.append(cell.center(self.cols_width[i]))
					else:
						raise ValueError("Invalid alignment '{}'".format(align))
				output += self.col_sep.join([str(c) for c in cells]) + '\n'
				if self.row_sep:
					output += self.join.join([
						(self.row_sep * width)[:width] for width in self.cols_width
					]) + '\n'
			else:
				row = str(row)
				output += self.join.join([
					(row * width)[:width] for width in self.cols_width
				]) + '\n'
		return output



# vim: ts=4 sw=4 noet
