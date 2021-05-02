#!/usr/bin/python3
import sys
import requests
import urllib.parse

from ego.module import EgoModule
from mediawiki.cli_parser import wikitext_parse


class Module(EgoModule):
	def add_arguments(self, parser):
		parser.add_argument("wiki_page", help="The name of a wiki page")

	def handle(self):
		try:
			url = (
				"https://www.funtoo.org/api.php?action=query&prop=revisions&rvprop=content&format=json&formatversion=2&titles=%s"
				% urllib.parse.quote(self.options.wiki_page)
			)
			print(url)
			wikitext_page = requests.get(url).json()["query"]["pages"][0]["revisions"][0]["content"]
			wikitext_parse(wikitext_page, sys.stdout)
		except BrokenPipeError:
			# this gets rid of ugly broken pipe message from modules:
			sys.stderr.close()
			sys.exit(1)


# vim: ts=4 noet sw=4
