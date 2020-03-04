#!/usr/bin/env python3

# Ego Helpers module.
#
# Copyright 2017-2020 Funtoo Solutions, Inc., Daniel Robbins and contributors.
# See LICENSE.txt for terms of distribution.

import sys
import textwrap
import shutil

verbosity = 1

if sys.stdout.isatty():
	is_tty = True
else:
	is_tty = False

term_size = shutil.get_terminal_size((80, 20))

def ago(hub, diff):

	"""
	Return a English string specifying how long ago something happened for a timedelta.
	"""

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

def depluralize(hub, s):
	if s[-1] == "s":
		return s[:-1]
	else:
		return s

class ColorType(str):
	pass

PURPLE = ColorType('\033[35m' if is_tty else "")
CYAN = ColorType('\033[36m' if is_tty else "")
DARKCYAN = ColorType('\033[36m' if is_tty else "")
DARKBLUEBG = ColorType('\033[44m' if is_tty else "")
BLUE = ColorType('\033[34m' if is_tty else "")
GREEN = ColorType('\033[32m' if is_tty else "")
YELLOW = ColorType('\033[33m' if is_tty else "")
RED = ColorType('\033[31m' if is_tty else "")
BOLD = ColorType('\033[1m' if is_tty else "")
UNDERLINE = ColorType('\033[4m' if is_tty else "")
END = ColorType('\033[0m' if is_tty else "")
AUTOFLUSH = ColorType("")

def purple(hub, text):
	return colorize(PURPLE, text)

def cyan(hub, text):
	return colorize(CYAN, text)

def darkcyan(hub, text):
	return colorize(DARKCYAN, text)

def blue(hub, text):
	return colorize(BLUE, text)

def green(hub, text):
	return colorize(GREEN, text)

def yellow(hub, text):
	return colorize(YELLOW, text)

def red(hub, text):
	return colorize(RED, text)

def bold(hub, text):
	return colorize(BOLD, text)

def underline(hub, text):
	return colorize(UNDERLINE, text)

def default(hub, text):
	return colorize(END, text)

def colorize(color, text):
	return color + text + END

def mesg(msgtype, msg, entry=None):
	global term_size
	""" prints different types of messages to the console """
	outstr = None
	if msgtype == "debug":
		if verbosity > 1:
			outstr = "{G} *{O} {m}".format(G=GREEN, O=END, m=msg)
		else:
			return
	elif msgtype in ["norm", "info"]:
		outstr = "{G} *{O} {m}".format(G=GREEN, O=END, m=msg)
	elif msgtype == "boot":
		if entry is None:
			outstr = "           {m}".format(m=msg)
		else:
			outstr = "          {entry:2d} {m}".format(entry=entry, m=msg)
	elif msgtype == "attemptboot":
		outstr = "{Y} ATTEMPT >{entry:2d} {B}{G}{m}{O}".format(entry=entry, B=BOLD, Y=YELLOW, G=GREEN, m=msg, O=END)
	elif msgtype == "defboot":
		if entry is None:
			outstr = "{C} DEFAULT > {G}{m}{O}".format(C=CYAN, G=GREEN, m=msg, O=END)
		else:
			outstr = "{C} DEFAULT >{entry:2d} {G}{m}{O}".format(entry=entry, C=CYAN, G=GREEN, m=msg, O=END)
	elif msgtype == "note":
		outstr = "{R} * NOTE:  {O} {m}".format(R=CYAN, O=END, m=msg)
	elif msgtype == "warn":
		outstr = "{R} * WARN:  {O} {m}".format(R=RED, O=END, m=msg)
	elif msgtype == "fatal" or True:
		outstr = "{R} * ERROR: {O} {m}".format(R=RED, O=END, m=msg)
	if outstr:
		print(textwrap.fill(outstr, term_size[0], initial_indent=" ", subsequent_indent="          "))

def header(hub, info):
	print("\n=== " + BOLD + GREEN + info + END + ": ===\n")

def _output(hub, message, err=False):
	message = str(message)
	if not message.endswith('\n'):
		message += '\n'
	out = sys.stderr if err else sys.stdout
	out.write(message)
	out.flush()

def debug(hub, message):
	"""Output debug message to stdout. Auto-append newline if missing"""
	if verbosity > 1:
		_output(message)

def log(hub, message):
	"""Output message to stdout. Auto-append newline if missing."""
	if verbosity > 0:
		_output(message)

def echo(hub, message):
	"""Output message as-is to stdout."""
	if verbosity > 0:
		sys.stdout.write(str(message))
		sys.stdout.flush()

def warning(hub, message):
	"""Output warning message to stdout. Auto-append newline if missing."""
	if verbosity > -1:
		_output(yellow("WARNING: " + str(message)))

def error(hub, message):
	"""Output error message to stderr. Auto-append newline if missing."""
	if verbosity > -1:
		_output(red("ERROR: " + str(message)), err=True)

def fatal(hub, message, exit_code=1):
	"""Output error message to stderr and exit. Auto-append newline if missing."""
	error(message)
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
				default(' ' * self.lpad) + c + (' ' * self.rpad)
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
