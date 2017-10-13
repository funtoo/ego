#!/usr/bin/python3

# MediaWiki Parser Mark 7
#
# Copyright 2017 Daniel Robbins and Funtoo Solutions, Inc.
# See LICENSE.txt for terms of distribution. 

import shutil
import mwparserfromhell
import html
import subprocess
from tabulate_color import tabulate
from ego_helpers import *
import re

rows, columns = subprocess.check_output(['stty', 'size']).decode().split()
term_size = shutil.get_terminal_size((100,20))
text_width = min(int(columns) - 1, 140)

class TextType(str):
	pass

class WikiTextWord(str):
	pass

class OutputPadding(str):
	def __repr__(self):
		return "<OUTPUTPADDING>"

class WikiTextSegment(list):
	pass

class WikiTextSpace(str):
	def __repr__(self):
		return "<SPACE>"

class WikiTextNewLine(str):

	def __repr__(self):
		return "<NEWLINE>"

class WikiTextNewBlock(str):

	def __repr__(self):
		return "<NEWBLOCK>"

class TableStart(object):
	pass

class TableEnd(object):
	pass

class TableRowStart(object):
	pass

class TableDataStart(object):
	pass

class TableRowEnd(object):
	pass

class TableDataEnd(object):
	pass

class TableHeaderStart(object):
	pass

class TableHeaderEnd(object):
	pass


ignore_nodes = [ mwparserfromhell.nodes.comment.Comment ]
ignore_tags = [ "languages" ]
ignore_templates = [ "articlefooter", "#widget:addthis", "#layout:doc" ]
ignore_magic_words = [ "__NOTITLE__", "__TOC__", "__NOTOC__" ]

def file_render(console_lines):

	# This function accepts a list of lines from a {{file}} template
	# and renders these lines to output. It returns a string.

	outstr = "\n"

	if len(console_lines) and console_lines[0] == "":
		# remove initial newline
		del console_lines[0]
	while len(console_lines) and console_lines[-1] == "":
		del console_lines[-1]

	for line in console_lines:
		outstr += "  " + Color.CYAN + line + "\n"
	return outstr 

console_re = re.compile("##!?([ibcgry]|bl)##")

def console_render(console_lines):
	global console_re
	global text_width

	# This function accepts a list of lines from a console tag or template and
	# renders them to the Linux terminal, colorized. It returns a colorized
	# unicode string.

	if len(console_lines) and console_lines[0] == "":
		# remove initial newline
		del console_lines[0]
	while len(console_lines) and console_lines[-1] == "":
		# remove any trailing newlines
		del console_lines[-1]

	outstr = "\n"
	output_lines = []
	bg = Color.DARKBLUEBG

	colorswap = { 
		"##i##": Color.YELLOW,
		"##b##": Color.BOLD,
		"##c##": Color.CYAN,
		"##g##": Color.GREEN,
		"##bl##": Color.BLUE,
		"##r##": Color.RED,
		"##y##": Color.YELLOW
	}

	lines_with_colors = []

	for line in console_lines:
		line = html.unescape(line)
		line_with_colors = []

		# use regex to find colors in each line, and create a list of text snippets and colors:

		while True:
			match = console_re.search(line)
			if not match:
				# add remaining part
				line_with_colors += [ line ]
				break
			try:
				color = [ colorswap[match.group()] ]
			except KeyError:
				color = [ Color.END, bg ]
			line_with_colors += [ line[0:match.start()] ] +  color
			line = line[match.end():]

		line_len = 0
		line_pos = 0
		# colors for the beginning of lines:
		line_header = [ bg, Color.GREEN ]
		# line_set_wrapped is one or more lines created from the original line.

		line_set_wrapped = [ [] + line_header ]
		# we keep track of the last color applied, because we want to apply in case of line wraps
		last_color = None

		while line_pos < len(line_with_colors):

			# let's look for literal text that is longer than text_width, and convert it into multiple lines:

			item = line_with_colors[line_pos]
			if isinstance(item, ColorType):
				# colors don't have a length; append and continue
				line_set_wrapped[-1].append(item)
				if item != Color.END:
					# preserve color for word wrap
					last_color = item
				else:
					# re-activate background color after turning any other active colors off:
					line_set_wrapped[-1].append(bg)
					last_color = None
			else:
				while len(item):
					# this will split lines:
					chars_to_be_added_to_this_line = text_width - line_len
					string_to_be_added = item[0:chars_to_be_added_to_this_line]
					chars_actually_added = len(string_to_be_added)
					line_len += chars_actually_added
					# add what we can, remove what we added
					line_set_wrapped[-1].append(item[0:chars_actually_added])
					item = item[chars_actually_added:]
					if chars_actually_added == chars_to_be_added_to_this_line:
						# if we actually got to end of line, so create a new one:
						line_set_wrapped.append([] + line_header )
						if last_color:
							line_set_wrapped[-1].append(last_color)
						line_len = 0

			line_pos += 1

		# We have finished wrapping lines, but potentially our last line does not extend to the very end
		# of the console. Let's extend it so we get a nice background color going consistently to the right:

		if line_len < text_width:
			line_set_wrapped[-1].append(" " * ( text_width - line_len))

		output_lines += line_set_wrapped

	for line in output_lines:
		# these guys should already be appropriately wrapped
		for linepart in line:
				outstr += linepart
		outstr += "\n"
	if len(outstr) and outstr[-1] != Color.END:
		outstr += Color.END
	return outstr

def text_tokenize(node, prev_node=None):

	global ignore_tags, ignore_templates

	tx_out = WikiTextSegment()
	pos = 0
	if isinstance(prev_node, WikiTextSpace ):
		was_space = True
	else:
		was_space = False
	if isinstance(prev_node, WikiTextNewLine) or isinstance(prev_node, WikiTextNewBlock):
		was_newline = True
	else:
		was_newline = False

	was_newline = False
	while pos < len(node):
		if node[pos:pos+2] == "\n\n":
			if not was_newline:
				tx_out += [ WikiTextNewBlock() ]
			pos += 2
			was_newline = True
			was_space = False
		elif node[pos:pos+1] == "\n":
			if not was_newline:
				tx_out += [ WikiTextNewLine() ]
			pos += 1
			was_newline = True
			was_space = False
		elif node[pos:pos+1] == " ":
			if not was_space:
				tx_out += [ WikiTextSpace() ]
			pos += 1
			was_space = True
			was_newline = False
		else:
			word_start = pos
			while pos < len(node) and node[pos] not in [ " ", "\n" ]:
				pos += 1
			tx_out += [ WikiTextWord(node[word_start:pos]) ]
			was_space = False
			was_newline = False
	return tx_out

def getMainNodes(block_text):

	global ignore_magic_words
	global ignore_nodes

	# This function accepts input as a bunch of unprocessed text from a file, in which
	# case it is parsed to wikicode, or already-parsed wikicode.

	# It will go through the wikicode and yield the main elements we are interested in
	# parsing, and stripping out the things we don't care about, like comments and
	# embedded <translate> tags. Results are yielded to the caller.

	if type(block_text) != mwparserfromhell.wikicode.Wikicode:
		wikicode = mwparserfromhell.parse(str(block_text))
	else:
		wikicode = block_text
	# look at our top-level nodes we have to handle
	prev_node = None
	for n in wikicode.nodes:
		if type(n) in ignore_nodes:
			continue
			#yield mwparserfromhell.nodes.text.Text("\n")
		elif type(n) == mwparserfromhell.nodes.tag.Tag and n.tag == "translate":
			for n2 in mwparserfromhell.parse(n.contents).nodes:
				if type(n2) in ignore_nodes:
					continue
				else:
					yield n2
		elif type(n) == mwparserfromhell.nodes.text.Text:
			for bad_word in ignore_magic_words:
				n = n.replace(bad_word, "")
			n = mwparserfromhell.nodes.text.Text(n)
			yield text_tokenize(n, prev_node)
		else:
			yield n
		prev_node = n

class TextAccumulator(object):

	def __init__(self,wrap):
		self.txlist = []
		self.wrap = wrap
		self.padding = True
		self.table_object = []
		self.output_redirect = False
		self.header_object = []
		self.colors = set()
		self.rowstart = True

	def append(self, item):
		if type(item) == list or isinstance(item, WikiTextSegment):
			self.txlist += item
		else:
			self.txlist.append(item)

	@property
	def empty(self):
		return len(self.txlist) == 0

	def tableEnd(self):
		table_out = "\n" + tabulate(self.table_object, tablefmt="fancy_grid", headers=self.header_object if len(self.header_object) else ()) + "\n"
		self.output_redirect = False
		self.table_object = []
		self.header_object = []
		return table_out

	def tableStart(self):
		self.table_object = []
		self.header_object = []

	def tableRowStart(self):
		self.rowstart = True

	def tableDataEnd(self):
		self.flush()

	def tableDataStart(self):
		# create new blank string for output
		if self.rowstart:
			# create new 'row' for output
			self.table_object.append([])
			self.rowstart = False
		self.output_redirect = "table"
		self.table_object[-1].append("")

	def setHeaders(self, headers):
		self.header_object = headers
	
	def tableHeaderStart(self):
		self.output_redirect = "header"
		self.header_object.append("")

	def tableHeaderEnd(self):
		self.flush()
		self.output_redirect = False

	def flush(self):
		global color
		asciipos = 0
		outstr = ""
		prev_item = None

		if self.output_redirect != False:
			wrap = round(( self.wrap -1 ) / 2)
		else:
			wrap = self.wrap
		#print(self.txlist)

		# Ingore initial NewBlocks, NewLines and Space in a block:
		while len(self.txlist) > 1 and (
				isinstance(self.txlist[0], WikiTextNewBlock) or
				isinstance(self.txlist[0], WikiTextNewLine) or
				isinstance(self.txlist[0], WikiTextSpace)
			):
			self.txlist.pop(0)

		# Ignoring trailing newline will mess up lists.
		while len(self.txlist) and (
				isinstance(self.txlist[-1], WikiTextNewBlock) or
				isinstance(self.txlist[-1], WikiTextSpace)
			):
			self.txlist.pop()
		item = None
		count = 0
		# count of last item
		last_count = len(self.txlist) - 1
		while len(self.txlist):
			item = self.txlist.pop(0)
			if isinstance(item, WikiTextSegment) or type(item) == list:
				self.txlist = item + self.txlist
				continue
			elif isinstance(item, OutputPadding):
				asciipos = 0
				count = 0
			elif isinstance(item, WikiTextWord):
				if len(item) + asciipos > wrap:
					if len(self.colors):
						# end colors at end of line
						outstr += Color.END
					asciipos = len(item)
					outstr += "\n" 
					for c in self.colors:
						# restart colors on new line
						outstr += c
					outstr += item
				else:
					outstr += item
					asciipos += len(item)
			elif isinstance(item, WikiTextSpace) or isinstance(item, WikiTextNewLine):
				#if isinstance(prev_item, WikiTextNewBlock):
				#	outstr += '\n\n'
				#	asciipos =0
				#	count = 0
				if isinstance(prev_item, WikiTextNewLine):
					# This is duplicate-skip logic.
					continue
				if count == 0:
					# Skip initial newline
					continue
				if asciipos == 0:
					# Skip newline if we are already at beginning of line
					continue
				elif asciipos < wrap:
					if isinstance(item, WikiTextSpace):
						outstr += " "
						asciipos += 1
					else:
						outstr += "\n"
						asciipos = 0
			elif isinstance(item, WikiTextNewLine):
				#pass HACK
				outstr += '\n'
				asciipos = 0
			elif isinstance(item, ColorType):
				if item == Color.END:
					self.colors = set()
				else:
					self.colors.add(item)
				outstr += item
			elif isinstance(item, WikiTextNewBlock):
				if count != 0 and count != last_count:
					# not at beginning or end, but in the middle
						outstr += '\n\n'
						asciipos = 0
						count = 0

			prev_item = item
			count += 1

		if isinstance(item, WikiTextNewBlock):
			# first, last item? was new block, respect it (for lists)
			outstr += "\n\n"
			asciipos = 0
			count = 0

		if self.output_redirect == "table" and len(self.table_object) and len(self.table_object[-1]):
			foo = self.table_object[-1][-1] + outstr
			#print("foo is", repr(foo))
			self.table_object[-1][-1] = foo
			outstr = ""
		elif self.output_redirect == "header" and len(self.header_object):
			self.header_object[-1] += outstr
			outstr = ""
		else:
			if outstr:
				if not outstr.endswith('\n'):
					outstr += '\n'
				if self.padding:
					outstr = '\n' + outstr
		self.padding = True
		return outstr

def parse(nodes, wrap=False, article_title=None):

	global ignore_tags, ignore_templates

	# This function accepts a list of nodes (or generator of nodes) as an argument, and will parse them.
	# In our main loop, if we are given a generator, we convert it to a list of nodes. Then as we are
	# processing each node, sometimes we "push" things to the beginning of the list of nodes if we find
	# things inside templates and tags that we want to have parsed immediately. This is how we avoid
	# recursion. It is a BAD idea to call parse() inside parse() and pass its output to accum_text. 
	# The world won't explode but your output won't be formatted quite right because it's not designed
	# to work that way.
	#
	# Instead, just prepend stuff to 'nodes' and it will get processed next iteration by the main loop.

	# The blocks of text returned to the caller are ready to be displayed on the console -- simply call
	# sys.stdout.write() with each result to see the rendered wikitext.

	accum_text = TextAccumulator(wrap=wrap)

	# Accum_text is used to collect text output for the current block that will be eventually yielded to
	# the caller.

	nodes = list(nodes)

	if len(nodes) == 1 and isinstance(nodes[0], WikiTextNewBlock):
		# skip empty new blocks to deal with extra spacing in source wikitext
		yield ""

	prev_node = None
	#for node in nodes:
	#		print(node, type(node), node.tag if hasattr(node,"tag") else "")
	while len(nodes):
		node = nodes.pop(0)
		if node == None:
			break
		if isinstance(node, ColorType):
			if node == Color.AUTOFLUSH:
				# flush toilet
				yield accum_text.flush()
			else:
				# someone pushed a color on to the parser stack -- process it as literal
				accum_text.append(node)
		elif isinstance(node, TableRowStart):
			accum_text.tableRowStart()
		elif isinstance(node, TableDataStart):
			accum_text.tableDataStart()
		elif isinstance(node, TableDataEnd):
			accum_text.tableDataEnd()
		elif isinstance(node, TableHeaderStart):
			accum_text.tableHeaderStart()
		elif isinstance(node, TableHeaderEnd):
			accum_text.tableHeaderEnd()
		elif type(node) == mwparserfromhell.nodes.heading.Heading:
			yield accum_text.flush()
			title = str(node.title).strip()
			if node.level == 1:
				yield Color.DARKCYAN + len(title) * "=" + Color.END + "\n"
				yield Color.CYAN + title + Color.END + "\n"
				yield Color.DARKCYAN + len(title) * "=" + Color.END + "\n"
			else:
				yield "\n" + Color.CYAN + title + Color.END + "\n"
		elif isinstance(node, WikiTextSegment):
			accum_text.append(node)
		elif type(node) == mwparserfromhell.nodes.text.Text:
			accum_text.append(text_tokenize(node, prev_node))
		elif type(node) == mwparserfromhell.nodes.wikilink.Wikilink:
			if node.title.startswith("File:"):
				nodes = [ Color.RED, text_tokenize("Image - Click to view: "), Color.END, mwparserfromhell.nodes.external_link.ExternalLink("http://www.funtoo.org/%s" % node.title) ] + nodes
			elif node.text:
				nodes = [ Color.UNDERLINE, Color.CYAN ] + list(getMainNodes(str(node.text).strip())) + [ Color.END ] + nodes
			else:
				nodes = [ Color.UNDERLINE, Color.CYAN ] + list(getMainNodes(str(node.title).strip())) + [ Color.END ] + nodes
		elif type(node) == mwparserfromhell.nodes.external_link.ExternalLink:
			if node.title:
				tx = [ Color.UNDERLINE, text_tokenize(str(node.title).strip(), prev_node), Color.END, WikiTextSpace(),
				       WikiTextWord("("), Color.CYAN, WikiTextWord(node.url), Color.END, WikiTextWord(")") ]
			else:
				tx = [ Color.CYAN, text_tokenize(str(node.url), prev_node), Color.END]
			accum_text.append(tx)
		elif type(node) == mwparserfromhell.nodes.tag.Tag:
			if node.tag in ignore_tags:
				continue
			elif node.tag == 'tr':
				# table row start
				nodes = [ TableRowStart() ] + list(getMainNodes(str(node.contents).strip())) + [ TableRowEnd() ] + nodes
			elif node.tag == 'div':
				# just render the contents of the div
				nodes = list(getMainNodes(str(node.contents))) + nodes
			elif node.tag == 'nowiki':
				nodes = text_tokenize(node.contents, prev_node) + nodes
			elif node.tag == 'td':
				nodes = [ TableDataStart() ] + list(getMainNodes(str(node.contents).strip())) + [ TableDataEnd() ] + nodes
			elif node.tag == 'dt':
				accum_text.append([ OutputPadding(), Color.RED ])
			elif node.tag == 'dd':
				accum_text.append([ Color.END ])
			elif node.tag == 'span':
				nodes = [ Color.GREEN ] + list(getMainNodes(str(node.contents))) + [ Color.END ] + nodes
			elif node.tag == 'th':
				nodes = [ TableHeaderStart() ] + list(getMainNodes(str(node.contents).strip())) + [ TableHeaderEnd() ] + nodes
			elif node.tag in [ 'b' ]:
				nodes = [ Color.BOLD ] + list(getMainNodes(str(node.contents))) + [ Color.END ] + nodes
			elif node.tag in [ 'code', 'tt', 'source' ]:
				nodes = [ Color.GREEN ] + list(getMainNodes(str(node.contents))) + [ Color.END ] + nodes
			elif node.tag == 'i':
				accum_text.append([ Color.UNDERLINE ])
				nodes = list(getMainNodes(str(node.contents))) + [ Color.END ] + nodes
			elif node.tag in [ 'console', 'pre', 'syntaxhighlight' ]:
				yield accum_text.flush()
				yield console_render(node.contents.split("\n"))
			elif node.tag == 'blockquote':
				# could be rendered better
				yield accum_text.flush()
				accum_text.append(Color.BOLD)
				nodes = list(getMainNodes(str(node.contents).strip())) + [ Color.END ] + nodes
			elif node.tag == "br":
				yield accum_text.flush()
			elif node.tag == 'li':
				# flush old block, and start a new one:
				yield accum_text.flush()
				accum_text.padding = False
				accum_text.append([Color.BOLD, WikiTextSpace(), WikiTextWord("*"), Color.END, WikiTextSpace()])
			else:
				yield accum_text.flush()
				accum_text.append([ Color.RED, WikiTextWord("[TAG"), WikiTextWord(node.tag if node.tag else "None"), WikiTextWord(":"), WikiTextSpace(), text_tokenize(node.contents) if node.contents else WikiTextWord("No-Contents"), Color.END, WikiTextWord("]") ])
		elif type(node) == mwparserfromhell.nodes.template.Template:
			tmp_name = node.name.lower().strip()
			if tmp_name in ignore_templates:
				continue
			elif tmp_name == "article":
				params = {}
				for param in node.params:
					param_name = param.split("=")[0]
					param_value = param[len(param_name)+1:].strip()
					params[param_name] = param_value

				for p in [ "Prev in Series", "Next in Series" ]:
					if p in params:
						nodes = [ Color.AUTOFLUSH, Color.RED, text_tokenize(p.split()[0] + " Article in Series: "), Color.END, mwparserfromhell.nodes.wikilink.Wikilink(params[p]), Color.AUTOFLUSH] + nodes

				if "Summary" in params:
					nodes = [ Color.GREEN, text_tokenize(params["Summary"]), Color.END ] + nodes
				art_t = article_title
				if "Subtitle" in params:
					art_t += " - " + params["Subtitle"]
				nodes = [ mwparserfromhell.nodes.heading.Heading(art_t, level=1) ] + nodes
			elif tmp_name == "tablestart":
				yield accum_text.flush()
				accum_text.tableStart()
			elif tmp_name == "tableend":
				yield accum_text.tableEnd()
			elif tmp_name in [ "2colhead", "3colhead" ]:
				accum_text.setHeaders(node.params)
			elif tmp_name in [ "2col" ]:
				nodes = [ TableRowStart(), TableDataStart() ] + list(getMainNodes(str(node.params[0]))) + [ TableDataEnd(), TableDataStart() ] + list(getMainNodes(str(node.params[1]))) + [ TableDataEnd(), TableRowEnd() ] + nodes
			elif tmp_name in [ "3col" ]:
				new_nodes = [ TableRowStart() ]
				for count in range(0,3):
					new_nodes += [ TableDataStart() ] + list(getMainNodes(str(node.params[count]))) + [ TableDataEnd() ]
				new_nodes += [ TableRowEnd() ] 
				nodes = new_nodes + nodes
			elif tmp_name == "bug":
				# below, we are essentially saying: "a bug template can be processed by pretending we immediately encounter an external link in the wikitext that is formatted like so:"
				nodes = [ mwparserfromhell.nodes.external_link.ExternalLink(url="https://bugs.funtoo.org/browse/" + str(node.params[0]), title="Bug " + str(node.params[0])) ] + nodes
			elif tmp_name == "createaccount":
				nodes = [ mwparserfromhell.nodes.external_link.ExternalLink(url="http://auth.funtoo.org:9093/new", title="Create a Funtoo Account") ] + nodes
			elif tmp_name == "console":
				yield accum_text.flush()
				yield console_render(str(node.get("body").value).split("\n"))
			elif tmp_name == "file":
				yield accum_text.flush()
				yield file_render(str(node.get("body").value).split("\n"))
			elif tmp_name == "c":
				nodes = [ Color.GREEN ] + list(getMainNodes(str(node.params[0]))) + [ Color.END ] + nodes
			elif tmp_name == "f":
				accum_text.append([ Color.CYAN ])
				nodes = list(getMainNodes(str(node.params[0]))) + [ Color.END ] + nodes
			elif tmp_name in [ "announce", "note", "fancyimportant", "fancynote", "important", "warning", "tip" ]:
				if tmp_name.startswith("fancy"):
					tmp_name = tmp_name[5:]
				yield accum_text.flush()
				note_text = str(node.params[0])
				if note_text.startswith("1=\n"):
					note_text = note_text[3:]
				# First we output the part of the template that we know how to output properly:
				accum_text.append([ Color.BOLD,  WikiTextWord(tmp_name.upper() + ":") , WikiTextSpace(), Color.END ])
				# we push the contents of the note to the front of the stack for parsing, so these things will get parsed
				# for the next loop iterations, before continuing with the remaining nodes of text for the rest of the 
				# document:
				a = list(getMainNodes(note_text))
				nodes = list(getMainNodes(note_text)) + [ Color.AUTOFLUSH ] + nodes
			elif tmp_name in [ "package" ]:
				accum_text.append([ WikiTextWord("wiki"), WikiTextSpace(), WikiTextWord("page"), WikiTextSpace(), WikiTextWord("for"), WikiTextSpace(), WikiTextWord("the"), WikiTextSpace(), Color.RED, WikiTextWord(node.params[0]), Color.END ])
			else:
				yield accum_text.flush()
				accum_text.append([ Color.RED, WikiTextWord("[TEMPLATE"), WikiTextWord(tmp_name), Color.END, WikiTextWord("]") ])
		prev_node = node
	yield accum_text.flush()

# vim: ts=4 sw=4 noet
