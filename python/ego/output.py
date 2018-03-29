#!/usr/bin/python3


# Ego Helpers module.
#
# Copyright 2017 Daniel Robbins and Funtoo Solutions, Inc.
# See LICENSE.txt for terms of distribution.

import sys
if sys.stdout.isatty():
	is_tty = True
else:
	is_tty = False

def ago(diff):

	"Return a English string specifying how long ago something happened for a timedelta."

	out = ""
	if diff.days == 1:
		out += "1 day"
	elif diff.days:
		out += "%s days" % diff.days
	if diff.seconds / 3600 >= 1:
		if len(out):
			out += " "
		if diff.seconds / 3600 == 1:
			out += "1 hour"
		else:
			out += "%.0f hours" % (diff.seconds / 3600)
	leftovers = diff.seconds % 3600
	if leftovers > 60:
		if len(out):
			out += " "
		if leftovers < 2:
			out += "1 minute"
		else:
			out += "%.0f minutes" % (leftovers / 60)
	if out != "":
		out += " ago"
	else:
		out = "just now"
	return out

def depluralize(str):
	if str[-1] == "s":
		return str[:-1]
	else:
		return str

class ColorType(str):
	pass

class Color(object):
	PURPLE = ColorType('\033[95m' if is_tty else "")
	CYAN = ColorType('\033[96m' if is_tty else "")
	DARKCYAN = ColorType('\033[36m' if is_tty else "")
	DARKBLUEBG = ColorType('\033[48;5;018m' if is_tty else "")
	BLUE = ColorType('\033[94m' if is_tty else "")
	GREEN = ColorType('\033[92m' if is_tty else "")
	YELLOW = ColorType('\033[93m' if is_tty else "")
	RED = ColorType('\033[91m' if is_tty else "")
	BOLD = ColorType('\033[1m' if is_tty else "")
	UNDERLINE = ColorType('\033[4m' if is_tty else "")
	END = ColorType('\033[0m' if is_tty else "")
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


class Output:

	verbosity = 1

	@classmethod
	def header(self, info):
		print("\n=== " + Color.BOLD + Color.GREEN + info + Color.END + ": ===\n")

	@classmethod
	def _output(cls, message, err=False):
		message = str(message)
		if not message.endswith('\n'):
			message += '\n'
		out = sys.stderr if err else sys.stdout
		out.write(message)
		out.flush()

	@classmethod
	def debug(cls, message):
		"""Output debug message to stdout. Auto-append newline if missing"""
		if cls.verbosity > 1:
			cls._output(message)

	@classmethod
	def log(cls, message):
		"""Output message to stdout. Auto-append newline if missing."""
		if cls.verbosity > 0:
			cls._output(message)

	@classmethod
	def echo(cls, message):
		"""Output message as-is to stdout."""
		if cls.verbosity > 0:
			sys.stdout.write(str(message))
			sys.stdout.flush()

	@classmethod
	def warning(cls, message):
		"""Output warning message to stdout. Auto-append newline if missing."""
		if cls.verbosity > -1:
			cls._output(Color.yellow("WARNING: " + str(message)))

	@classmethod
	def error(cls, message):
		"""Output error message to stderr. Auto-append newline if missing."""
		if cls.verbosity > -1:
			cls._output(Color.red("ERROR: " + str(message)), err=True)

	@classmethod
	def fatal(cls, message, exit_code=1):
		"""Output error message to stderr and exit. Auto-append newline if missing."""
		cls.error(message)
		sys.exit(exit_code)

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
