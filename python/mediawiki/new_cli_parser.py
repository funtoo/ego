#!/usr/bin/python3

import mwparserfromhell
import urllib.parse
import requests
import sys

ignore_nodes = [mwparserfromhell.nodes.comment.Comment]
ignore_tags = ["languages"]
ignore_magic_words = ["__NOTITLE__", "__TOC__", "__NOTOC__"]


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


def parse(node):
	global ignore_tags

	cur_level = 1

	if not isinstance(node, mwparserfromhell.nodes.Node):
		nodes = mwparserfromhell.parse(node).nodes
	else:
		nodes = node.nodes

	for node in nodes:

		# if type(node) == mwparserfromhell.nodes.tag.Tag and node.tag == "table":
		# 	for line in node.contents.split("\n"):
		# 		if line.startswith("!"):
		# 			continue
		# 		else:
		# 			for stuff in parse([line, "\n"], all_pages):
		# 				yield stuff
		if type(node) == mwparserfromhell.nodes.template.Template:
			yield node
		elif type(node) == mwparserfromhell.nodes.Tag and node.tag == "translate":
			# recurse
			for n in parse(node.contents):
				yield n
		elif type(node) == mwparserfromhell.nodes.Tag:
			print("TAG", node.tag)
			print("CONTENTS", node.contents)
			yield node
		elif isinstance(node, mwparserfromhell.nodes.comment.Comment):
			continue
		elif type(node) == mwparserfromhell.nodes.Heading:
			# expand any templates or other wikitext in the heading, using this same function...
			out = ""
			for obj in parse(node.title):
				out += str(obj)
			node.title = out
			cur_level = node.level
			yield node
		else:
			yield node


def wikitree(wikitext):

	# "Wikicode" are collections (lists) of nodes. Nodes can be more wikicode.
	# Nodes are individual wiki elements.

	wikicode = mwparserfromhell.parse(wikitext)
	for node in wikicode.nodes:
		yield node


def wikitext_parse(wikitext: str, category=None, all_pages=None):
	for el in parse(wikitree(wikitext)):
		yield el


wiki_page = "Install"
url = (
	"https://www.funtoo.org/api.php?action=query&prop=revisions&rvprop=content&format=json&formatversion=2&titles=%s"
	% urllib.parse.quote(wiki_page)
)
wikitext_page = requests.get(url).json()["query"]["pages"][0]["revisions"][0]["content"]

for node in wikitext_parse(wikitext_page):
	print("   ", type(node), str(node)[:80])
