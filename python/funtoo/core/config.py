# -*- coding: ascii -*-

# STATE OF THE CODE:
#
# 1. Templates need testing.
# 2. Line number data is collected for various things.
# 3. dump() will remember comments that appear outside sections and templates.
# 4. { } delimits a section, [ ] delimits a template.
# 5. Overall, most key functionality is implemented and just needs testing.
# 6. One exception is the exception code, which needs to be implemented.

import os
import sys
from collections import OrderedDict


class ConfigFileError(Exception):
	def __init__(self, *args):
		self.args = args
	
	def __str__(self):
		if len(self.args) == 1:
			return str(self.args[0])
		else:
			return "(no message)"


class ConfigFile:
	def __init__(self, fname=None, existing=True, msgs=None):
		
		# we use self.sections as the master list of sections, with their contents in self.obj. It is up to this class
		# to keep self.sections and self.obj in sync. self.sections is used so that the ordering of the sections can be
		# preserved when we dump the data.
		
		self.orderedObjects = []
		self.templates = {}
		self.sectionData = OrderedDict()
		self.sectionDataOrder = {}
		self.msgs = msgs if msgs is not None else []
		self.lineData = {
			"section": {},
			"sectionData": {},
			"template": {},
		}
		
		self.parent = None
		self.defaults = ""
		
		self.existing = existing
		self.fname = fname
		
		if self.existing and self.fileExists():
			fn = open(self.fname, "r")
			self.read(fn.readlines())
			fn.close()
	
	
	def deburr(self, str, delim=None):
		# remove surrounding quotes
		str = str.strip()
		if delim != None:
			str = str.rstrip(delim).rstrip()
		if len(str) > 2 and str[0] == '"' and str[-1] == '"':
			return str[1:-1]
		else:
			return str
	
	def fileExists(self):
		if not self.fname:
			return False
		if not os.path.exists(self.fname):
			return False
		return True
	
	def setParent(self, parent):
		"""
		The "parent" is currently a static setting that you would override
		in __init__() in the subclass. It specifies a ConfigFile object that
		is the logical "parent" of the current config file. The way this
		works in variable resolution is as follows. If we are looking for
		variable "foo/bar" in the current config file, and it is not defined,
		we will first call self.inherit() to see if a default value should be
		inherited from another section in *this* ConfigFile object (see
		self.inherit, below.) If self.inherit() returns None, or it returns a
		category name that has not been defined in this ConfigFile object
		(like let's say it returns "oni" but there is no "oni/bar" defined),
		then we take a look at self.parent to determine if there is a logical
		parent to this ConfigFile object. If so, and the requested original
		variable exists in that ConfigFile object, then we return the value
		from the parent ConfigFile object.

		Note that ConfigFile objects can be chained using the self.parent
		setting.
		Also note that self.dump() will only dump the contents of the current
		ConfigFile object, and will not accumulate any data that is stored in
		any parents.
		"""
		self.parent = parent
	
	def dump(self):
		lines = []
		for obj, name in self.orderedObjects:
			if obj == "section":
				lines.append("section {n} {{\n".format(n=name))
				for var in self.sectionDataOrder[name]:
					lines.append("  {v} {d}\n".format(v=var, d=self.sectionData[name][var]))
				lines.append("}\n")
				lines.append("\n")
			elif obj == "template":
				for line in self.templates[name]:
					lines.append(line)
			elif obj == "comment":
				lines.append(name)
		if len(lines) > 0 and lines[-1] == "\n":
			# remove extra trailing newline
			del lines[-1]
		return lines
	
	def printDump(self):
		for line in self.dump():
			sys.stdout.write(line)
	
	def write(self):
		if self.fname:
			base = os.path.dirname(self.fname)
			if not os.path.exists(base):
				os.makedirs(base)
			newf = open("{fn}.new".format(fn=self.fname), "w")
			for line in self.dump():
				newf.write(line)
			newf.close()
			if os.path.exists(self.fname):
				os.unlink(self.fname)
			os.rename("{fn}.new".format(fn=self.fname), self.fname)
	
	def readFromLines(self, lines):
		self.read(lines.split("\n"))
	
	"""
	self.orderedObjects =

	[ "section", "foo" ] [ "template", "bar" ] [ "comment", "# foasdflsdf asdl " ]

	self.templates = {}
	self.sectionData = { "foo" : { "bar": "alaksdf", "basl", "asdlkfds", }}
	self.sectionDataOrder = { "foo", [ "bar", "basl" ] }



	"""
	
	def read(self, lines):
		ln = 0
		while ln < len(lines):
			if lines[ln].lstrip()[:1] == "#" or lines[ln].lstrip() == "":
				# comment or whitespace (which is treated as a comment)
				self.orderedObjects.append(["comment", lines[ln]])
				ln += 1
				continue
			
			elif lines[ln].rstrip()[-1:] == "{":
				# section start
				section = self.deburr(lines[ln], "{")
				if section in self.sectionData:
					# duplicate section - bad
					raise ConfigFileError("Duplicate config file section \"{sect}\" on line {num}".format(sect=section, num=ln + 1))
				
				# Initialize internal section data store
				self.sectionData[section] = {}
				self.sectionDataOrder[section] = []
				
				# Record line number of section definition
				self.lineData["section"][section] = ln + 1
				
				ln += 1
				while ln < len(lines) and lines[ln].strip() != "}":
					# strip comments from variable line - these comments don't get preserved on dump()
					comfind = lines[ln].find("#")
					if comfind != -1:
						line = lines[ln][0:comfind]
					else:
						line = lines[ln]
					ls = line.split()
					if len(ls) == 0:
						# empty line, skip
						ln += 1
						continue
					
					# at least we have a variable name
					
					varname = ls[0]
					vardata = " ".join(ls[1:])
					
					if varname == "{":
						# this is illegal
						raise ConfigFileError("Illegal variable name \"{\" on line {num}".format(num=ln + 1))
					
					if len(ls) < 2 or (vardata == ""):
						# a variable but no data
						raise ConfigFileError("Variable name \"{name}\" has no data on line {num}".format(name=varname, num=ln + 1))
					
					# the following conditional block allows additional += lines to append to variables without
					# throwing an exception, as follows:
					#
					# foo {
					#   params root=auto
					#   params += init=/bin/bash
					# }
					#
					# Note that if this file is dumped (ie. written back to disk,) then the params will appear
					# as a single line. This is because the multi-line variable is expanded when the file is
					# read in, because it's easier that way.
					#
					# Also note that a single variable with an initial "+=" will be evaluated using a different
					# code path, at variable resolution time. An initial "+=" means "inherit from default section",
					# whereas successive "+="'s hit the code path here and mean "append to previously-defined
					# line."
					
					if varname in self.sectionData[section]:
						if ls[1] == "+=":
							self.sectionData[section][varname] += " {data}".format(data=" ".join(ls[2:]))
						else:
							raise ConfigFileError("Duplicate variable \"{name}\" on line {num}".format(name=varname, num=ln + 1))
					else:
						# record our variable data
						self.sectionDataOrder[section].append(varname)
						self.sectionData[section][varname] = vardata
					
					# record line number of variable data:
					self.lineData["sectionData"]["{sect}/{name}".format(sect=section, name=varname)] = ln + 1
					
					ln += 1
				
				self.orderedObjects.append(["section", section])
				ln += 1
			
			elif lines[ln].rstrip()[-1:] == "[":
				template = self.deburr(lines[ln], "[")
				
				if template in self.templates:
					# bad - duplicate template
					raise ConfigFileError("Duplicate template \"{tem}\" on line {num}".format(tem=template, num=ln + 1))
				self.lineData["template"][template] = ln + 1
				
				ln += 1
				tdata = []
				while ln < len(lines) and lines[ln].strip() != "]":
					tdata.append(lines[ln])
					ln += 1
				
				self.templates[template] = tdata
				self.orderedObjects.append(["template", template])
				ln += 1
			else:
				# no clue what this is
				raise ConfigFileError("Unexpected data \"{data}\" on line {num}".format(data=lines[ln], num=ln + 1))
	
	# IMPLEMENT THIS:
	
	def hasTemplate(self, template):
		if self.parent:
			return self.parent.hasTemplate(template) or template in self.templates
		else:
			return template in self.templates
	
	def hasLocalTemplate(self, template):
		return template in self.templates
	
	def hasItem(self, item):
		return self.item(item, varname=None, bool=True)
	
	def condSubItem(self, item, str):
		return self.subItem(item, str, cond=True)
	
	def condFormatSubItem(self, item, str):
		return self.formatSubItem(item, str, cond=True)
	
	def flagItemList(self, item):
		"""
		This method parses a variable line containing "foo bar -oni" into two sub-lists ([foo, bar], [oni])
		"""
		
		my_list = self.item(item).split()
		grab = []
		skip = []
		# put "foo" entries in grab, whereas "-bar" go in skip:
		for item in my_list:
			if item[0] == "-":
				skip.append(item[1:])
			else:
				grab.append(item)
		return grab, skip
	
	def getSections(self):
		# might want to add ability to see only local sections, vs. parent sections too.
		return list(self.sectionData.keys())
	
	def subItem(self, item, str, cond=False):
		"""
		Give this function "foo/bar" and "blah %s blah" and it will return "blah <value of foo/bar> blah"
		If cond=True, then we will zap the line (return "") if str points to a null ("") value
		"""
		
		if cond and not self.item(item, varname=None):
			return ""
		else:
			return str % self.item(item, varname=None)
	
	def formatSubItem(self, item, str, cond=False):
		"""
		Give this function "foo/bar" and "blah {s} blah" and it will return "blah <value of foo/bar> blah"
		If cond=True, then we will zap the line (return "") if str points to a null ("") value
		"""
		
		if cond and not self.item(item, varname=None):
			return ""
		else:
			return str.format(s=self.item(item, varname=None))
	
	def hasLocalItem(self, item):
		
		return self.item(item, varname=None, bool=True, parents=False)
	
	def __setitem__(self, key, value):
		
		# Need to throw exception if value already exists in parents?
		
		keysplit = key.split("/")
		section = "/".join(keysplit[:-1])
		varname = keysplit[-1]
		
		if not section in self.sectionData:
			# initialize internal data store
			self.sectionData[section] = {}
			self.sectionDataOrder[section] = []
			# add to our ordered objects list so we output this section at the end when we dump()
			self.orderedObjects.append(["section", section])
		
		self.sectionData[section][varname] = value
	
	def __getitem__(self, item):
		return self.item(item, varname=None)
	
	def inherit(self, section):
		"""
		Override this in the subclass.

		This allows customized inheritance behavior - given current
		section of "section", what section does it inherit from? Return a
		string name of section to inherit from, or None for no
		inheritance. For example, /etc/boot.conf's "Foobar Linux"
		section would inherit from the "default" section. Whereas some
		other config file's "graphics" section may inherit from
		"default/graphics".
		"""
		return None
	
	def template(self, section):
		# TODO: IMPLEMENT ME WITH INHERITANCE JUST LIKE self.item()
		if self.hasTemplate(section):
			return self.templates[section]
		else:
			return None
	
	def item(self, section, varname=None, bool=False, parents=True, defaults=True):
		"""
		This is the master function for returning the value of a
		ConfigFile item, and also to get a boolean value of whether a
		ConfigFile item exists. It has a number of parameters which
		control its behavior, defined below:

		If bool=True, we return a True/False value depending on whether the object exists.
		If bool=False, we return the actual config file value. False is the default.

		If parents=True, we look at parents. It is true by default.
		If parents=False, we ignore any parents for both boolean and actual value calculations.

		If defaults=True, we look at any default sections in the file that are defined via self.inherit() when retrieving values. Default.
		If defaults=False, we ignore any default sections defined via self.inherit().

		if varname==None, then cat/name are autogenerated from the value in cat, which is expected to be "foo/bar"
		"""
		
		if varname is None:
			keysplit = section.split("/")
			section = "/".join(keysplit[:-1])
			varname = keysplit[-1]
		
		defsection = None
		if defaults:
			defsection = self.inherit(section)
		
		if section in self.sectionData and varname in self.sectionData[section]:
			if bool:
				return True
			elif (len(self.sectionData[section][varname].split()) >= 2) and (self.sectionData[section][varname].split()[0] == "+="):
				# we have data, and we have the append operator -- set realdata to everything minus the initial "+="
				realdata = " ".join(self.sectionData[section][varname].split()[1:])
				if defsection in self.sectionData and varname in self.sectionData[defsection]:
					# ah! We have a default value defined in our local config file. - combine with parent value
					return self.sectionData[defsection][varname] + " " + realdata
				elif parents and self.parent and self.parent.hasItem("{sect}/{name}".format(sect=defsection, name=varname)):
					# ah! one of our parents has a default section defined - combine with parent value
					return self.parent.item(defsection, varname) + " " + realdata
				else:
					# couldn't find a default section, so just return realdata
					return realdata
			else:
				# no append operator, so we just return our literal data
				return self.sectionData[section][varname]
		elif defsection and defsection in self.sectionData and varname in self.sectionData[defsection]:
			if bool:
				return True
			else:
				# only default value defined
				return self.sectionData[defsection][varname]
		else:
			# no value defined
			if parents and self.parent:
				return self.parent.item(section, varname, bool=bool)
			elif bool:
				return False
			else:
				return ""
