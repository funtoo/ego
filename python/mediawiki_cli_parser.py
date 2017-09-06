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

rows, columns = subprocess.check_output(['stty', 'size']).decode().split()
term_size = shutil.get_terminal_size((100,20))
text_width = int(columns) - 1
if text_width > 140:
	text_width = 140

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
		outstr += "  " + color.CYAN + line + "\n"
	return outstr 

def console_render(console_lines):

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
	bg = color.DARKBLUEBG

	colorswap = { 
		"##i##": color.YELLOW,
		"##b##": color.BOLD,
		"##c##": color.CYAN,
		"##g##": color.GREEN,
		"##!c##": color.END + bg,
		"##!g##": color.END + bg,
		"##!b##": color.END + bg,
	}
	for line in console_lines:
		line = html.unescape(line)
		real_length = len(line)
		line = color.GREEN + bg + line
		for key, esc_val in colorswap.items():
			try:
				while True:
					line.index(key)
					line = line.replace(key, esc_val, 1)
					real_length -= len(key) 
			except ValueError:
				pass
		line += bg
		if real_length < text_width:
			line += (text_width - real_length) * " "
		line += color.END
		outstr += line + "\n"
	return outstr

def text_tokenize(node):

	global ignore_tags, ignore_templates

	tx_out = WikiTextSegment()
	pos = 0
	was_space = False
	while pos < len(node):
		if node[pos:pos+2] == "\n\n":
			if not was_space:
				tx_out += [ WikiTextNewBlock() ]
			pos += 2
			was_space = True
		elif node[pos:pos+1] == "\n":
			if not was_space:
				tx_out += [ WikiTextNewLine() ]
			pos += 1
			was_space = True
		elif node[pos:pos+1] == " ":
			if not was_space:
				tx_out += [ WikiTextSpace() ]
			pos += 1
			was_space = True
		else:
			word_start = pos
			while pos < len(node) and node[pos] not in [ " ", "\n" ]:
				pos += 1
			tx_out += [ WikiTextWord(node[word_start:pos]) ]
			was_space = False
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
			yield text_tokenize(n)
		else:
			yield n

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

		while len(self.txlist) > 1 and (
				isinstance(self.txlist[0], WikiTextNewBlock) or
				isinstance(self.txlist[0], WikiTextNewLine) or
				isinstance(self.txlist[0], WikiTextSpace)
			):
			self.txlist.pop(0)
		
		while len(self.txlist) and (
				isinstance(self.txlist[-1], WikiTextNewBlock) or
				isinstance(self.txlist[-1], WikiTextNewLine) or
				isinstance(self.txlist[-1], WikiTextSpace)
			):
			self.txlist.pop()
		item = None
		count = 0
		while len(self.txlist):
			item = self.txlist.pop(0)
			if isinstance(item, WikiTextSegment) or type(item) == list:
				self.txlist = item + self.txlist
				continue
			elif isinstance(item, OutputPadding):
				outstr += '\n\n'
				asciipos = 0
				count = 0
			elif isinstance(item, WikiTextWord):
				if len(item) + asciipos > wrap:
					if len(self.colors):
						# end colors at end of line
						outstr += color.END
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
				if isinstance(prev_item, WikiTextNewBlock):
					outstr += '\n\n'
					asciipos =0
					count = 0
				elif isinstance(prev_item, WikiTextNewLine) or isinstance(prev_item, WikiTextSpace):
					continue
				if count == 0:
					continue
				if asciipos == 0:
					continue
				elif asciipos < wrap:
					outstr += " "
					asciipos += 1
			elif isinstance(item, WikiTextNewLine):
				pass
			elif isinstance(item, ColorType):
				if item == color.END:
					self.colors = set()
				else:
					self.colors.add(item)
				outstr += item
			elif isinstance(item, WikiTextNewBlock):
				#if not len(self.txlist):
				#	# last item, so handle it
				#	outstr += '\n\n'
				#	asciipos = 0
				#	count = 0
				#else:
				#	# handled by wikitextword condition
				pass
			prev_item = item
			count += 1

		if isinstance(item, WikiTextNewBlock):
			# first, last item? was new block, respect it (for lists)
			outstr += "\n\n"
			asciipos = 0
			count = 0

		if self.output_redirect == "table" and len(self.table_object) and len(self.table_object[-1]):
			foo = self.table_object[-1][-1] + outstr
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

	while len(nodes):
		node = nodes.pop(0)
		if node == None:
			break
		if isinstance(node, ColorType):
			if node == color.AUTOFLUSH:
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
				yield color.DARKCYAN + len(title) * "=" + color.END + "\n"
				yield color.CYAN + title + color.END + "\n"
				yield color.DARKCYAN + len(title) * "=" + color.END + "\n"
			else:
				yield "\n" + color.CYAN + title + color.END + "\n"
		elif isinstance(node, WikiTextSegment):
			accum_text.append(node)
		elif type(node) == mwparserfromhell.nodes.text.Text:
			accum_text.append(text_tokenize(node))
		elif type(node) == mwparserfromhell.nodes.wikilink.Wikilink:
			if node.title.startswith("File:"):
				nodes = [ color.RED, text_tokenize("Image - Click to view: "), color.END, mwparserfromhell.nodes.external_link.ExternalLink("http://www.funtoo.org/%s" % node.title) ] + nodes
			elif node.text:
				nodes = [ color.UNDERLINE, color.CYAN ] + list(getMainNodes(str(node.text).strip())) + [ color.END ] + nodes
			else:
				nodes = [ color.UNDERLINE, color.CYAN ] + list(getMainNodes(str(node.title).strip())) + [ color.END ] + nodes
		elif type(node) == mwparserfromhell.nodes.external_link.ExternalLink:
			if node.title:
				tx = [ color.UNDERLINE, text_tokenize(str(node.title).strip()), color.END, WikiTextSpace(), WikiTextWord("("), color.CYAN, WikiTextWord(node.url), color.END, WikiTextWord(")") ]
			else:
				tx = [ color.CYAN, text_tokenize(str(node.url)), color.END]
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
				nodes = text_tokenize(node.contents) + nodes
			elif node.tag == 'td':
				nodes = [ TableDataStart() ] + list(getMainNodes(str(node.contents).strip())) + [ TableDataEnd() ] + nodes
			elif node.tag == 'dt':
				accum_text.append([ OutputPadding(), color.RED ])
			elif node.tag == 'dd':
				accum_text.append([ color.END ])
			elif node.tag == 'span':
				nodes = [ color.GREEN ] + list(getMainNodes(str(node.contents))) + [ color.END ] + nodes
			elif node.tag == 'th':
				nodes = [ TableHeaderStart() ] + list(getMainNodes(str(node.contents).strip())) + [ TableHeaderEnd() ] + nodes
			elif node.tag in [ 'b' ]:
				nodes = [ color.BOLD ] + list(getMainNodes(str(node.contents))) + [ color.END ] + nodes
			elif node.tag in [ 'code', 'tt', 'source' ]:
				nodes = [ color.GREEN ] + list(getMainNodes(str(node.contents))) + [ color.END ] + nodes
			elif node.tag == 'i':
				accum_text.append([ color.UNDERLINE ])
				nodes = list(getMainNodes(str(node.contents))) + [ color.END ] + nodes
			elif node.tag in [ 'console', 'pre', 'syntaxhighlight' ]:
				yield accum_text.flush()
				yield console_render(node.contents.split("\n"))
			elif node.tag == 'blockquote':
				# could be rendered better
				yield accum_text.flush()
				accum_text.append(color.BOLD)
				nodes = list(getMainNodes(str(node.contents).strip())) + [ color.END ] + nodes
			elif node.tag == "br":
				yield accum_text.flush()
			elif node.tag == 'li':
				# flush old block, and start a new one:
				yield accum_text.flush()
				accum_text.padding = False
				accum_text.append([color.BOLD, WikiTextSpace(), WikiTextWord("*"), color.END])
			else:
				yield accum_text.flush()
				accum_text.append([ color.RED, WikiTextWord("[TAG"), WikiTextWord(node.tag if node.tag else "None"), WikiTextWord(":"), WikiTextSpace(), text_tokenize(node.contents) if node.contents else WikiTextWord("No-Contents"), color.END, WikiTextWord("]") ])
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
						nodes = [ color.AUTOFLUSH, color.RED, text_tokenize(p.split()[0] + " Article in Series: "), color.END, mwparserfromhell.nodes.wikilink.Wikilink(params[p]), color.AUTOFLUSH] + nodes

				if "Summary" in params:
					nodes = [ color.GREEN, text_tokenize(params["Summary"]), color.END ] + nodes
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
				nodes = [ color.GREEN ] + list(getMainNodes(str(node.params[0]))) + [ color.END ] + nodes
			elif tmp_name == "f":
				accum_text.append([ color.CYAN ])
				nodes = list(getMainNodes(str(node.params[0]))) + [ color.END ] + nodes
			elif tmp_name in [ "announce", "note", "fancyimportant", "fancynote", "important", "warning", "tip" ]:
				if tmp_name.startswith("fancy"):
					tmp_name = tmp_name[5:]
				yield accum_text.flush()
				note_text = str(node.params[0])
				if note_text.startswith("1=\n"):
					note_text = note_text[3:]
				# First we output the part of the template that we know how to output properly:
				accum_text.append([ color.BOLD,  WikiTextWord(tmp_name.upper() + ":") , WikiTextSpace(), color.END ])
				# we push the contents of the note to the front of the stack for parsing, so these things will get parsed
				# for the next loop iterations, before continuing with the remaining nodes of text for the rest of the 
				# document:
				a = list(getMainNodes(note_text))
				nodes = list(getMainNodes(note_text)) + [ color.AUTOFLUSH ] + nodes
			elif tmp_name in [ "package" ]:
				accum_text.append([ WikiTextWord("wiki"), WikiTextSpace(), WikiTextWord("page"), WikiTextSpace(), WikiTextWord("for"), WikiTextSpace(), WikiTextWord("the"), WikiTextSpace(), color.RED, WikiTextWord(node.params[0]), color.END ])
			else:
				yield accum_text.flush()
				accum_text.append([ color.RED, WikiTextWord("[TEMPLATE"), WikiTextWord(tmp_name), color.END, WikiTextWord("]") ])
		prev_node = node
	yield accum_text.flush()

# vim: ts=4 sw=4 noet
