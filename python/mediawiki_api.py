#!/usr/bin/python3

import sys
import configparser
import requests
from datetime import date

# MediaWiki API Mark 3
#
# Copyright 2017 Daniel Robbins and Funtoo Solutions, Inc.
# See LICENSE.txt for terms of distribution. 

class Wiki(object):

	def __init__(self,url):

		self.url = url
		self.cookies = {}
		self.logged_in = False
		self.tokens = []
		self.failed_pages = []

	def login(self,user,password):
		data = { 'format' : 'json', 'action' : 'login', 'lgname' : user, 'lgpassword': password }
		r = requests.post(self.url, params=data)
		j = r.json()
		if ('login' in j) and ('result' in j['login']):
			self.cookies = r.cookies
			if j['login']['result'] == "Success":
				self.logged_in = True
			elif j['login']['result'] == "NeedToken":
				data['lgtoken'] = j['login']['token']
				r = requests.post(self.url, params=data, cookies=self.cookies)
				j = r.json()
				if j['login']['result'] == "Success":
					self.cookies.update(r.cookies)
					self.logged_in = True
		return self.logged_in

	def show_cookies(self):
		return dict(self.cookies)

	def getTokens(self,kinds=["edit","import"]):
		if not self.logged_in:
			return False
		data = { 'format' : 'json', 'action' : 'tokens' , 'type' : '|'.join(kinds) }
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'tokens' in j:
			self.tokens = j['tokens']
		return self.tokens

	def getAllPages(self, namespace=0, limit=10000):
		data = { 'format' : 'json', 'action' : 'query', 'list' : 'allpages', 'apnamespace' : namespace, 'aplimit' : limit }
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'allpages' in j['query']:
			return j['query']['allpages']

	def getRecentChanges(self, args={}):
		data = { 'format' : 'json', 'action' : 'query', 'list' : 'recentchanges' }
		data.update(args)
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'recentchanges' in j['query']:
			return j['query']['recentchanges']

	def getPage(self, title):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'revisions', 'rvprop' : 'content' }
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'pages' in j['query']:
			w = j['query']['pages']
			if 'revisions' in w[list(w.keys())[0]]:
				return w[list(w.keys())[0]]["revisions"][0]["*"]
		return None

	def putPage(self, title, content):
		data = { 'format' : 'json', 'action' : 'edit', 'title' : title, 'text' : content, 'contentformat' : 'text/x-wiki', 'token' : self.tokens["edittoken"]}
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'edit' in j and 'result' in j['edit'] and j['edit']['result'] == 'Success':
			return True
		return False

	def importPage(self, title, interwiki, namespace=0, failcount=3):
		data = { 'format' : 'json', 'action' : 'import', 'interwikisource' : interwiki, 'interwikipage' : title, 'namespace' : namespace, 'fullhistory' : 'yes', 'token' : self.tokens["importtoken"] }
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'import' in j and 'revisions' in j['import'][0]:
			print("Imported %s" % title)
			return True
		else:
			print("Failed to import %s" % title)
			if failcount > 0:
				# retry by recursing a certain number of times:
				if self.importPage(title, interwiki, namespace, failcount - 1) == True:
					return True
			else:
				self.failed_pages.append(title)
				return False

	def getPageLinks(self, title, ns=None):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'links' }
		if ns != None:
			data["plnamespace"] = ns
		data['pllimit'] = 1000
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		return j

	def getPageImages(self, title):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'images' }
		data['imlimit'] = 1000
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'pages' in j['query']:
			k = j['query']['pages'].keys()
			if len(k) == 1:
				i = j['query']['pages'][list(k)[0]]
				if 'images' in i:
					return i['images']
		return []

	def getImageURL(self, title):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'imageinfo', 'iiprop' : 'url' }
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'pages' in j['query']:
			k = j['query']['pages'].keys()
			if len(k) == 1:
				i = j['query']['pages'][list(k)[0]]
				if 'imageinfo' in i and 'url' in i['imageinfo'][0]:
					return i['imageinfo'][0]['url']
		return None

	def importPageImages(self, title, source_wiki, interwiki):
		"specify a page -- find all image links and upload them into this wiki."
		print("Attempting to import pags \"%s\" images..." % title)
		# Attempt to grab images referenced on this page -- even though they may not exist.
		images = source_wiki.getPageImages(title)
		for i in images:
			print("  Attempting to import image \"%s\" (referenced)..." % i['title'],end='')
			surl = source_wiki.getImageURL(i['title'])
			if surl == None:
				print("Couldn't get URL for image.")
				continue
			#filename does not have File: ns prefix -- so we strip it:
			fn = ':'.join(i['title'].split(":")[1:])
			result = self.uploadFileFromURL(fn, surl)
			if result == False:
				print("Couldn't upload image.")
				continue
			print("Uploaded image!")

	def importPageAndImages(self, title, source_wiki, interwiki, namespace=0, failcount=3):
		"specify a page -- import the page, and if successful, also transwiki all image links."
		result = self.importPage(title, interwiki, namespace, failcount)
		if result == True:
			self.importPageImages(title, source_wiki, interwiki)

	def exportXML(self, title):
		data = { 'format' : 'json', 'action': 'query' , 'titles' : title, 'export' : 'yes', 'exportnowrap' : 'yes' }
		r = requests.post(self.url, params=data, cookies=self.cookies)
		return r.text

	def uploadFileFromURL(self, filename, url):
		data = { 'format' : 'json', 'action' : 'upload', 'url' : url, 'filename' : filename, 'token' : self.tokens["edittoken"] }
		print(data)
		r = requests.post(self.url, params=data, cookies=self.cookies)
		j = r.json()
		print(j)
		if ('upload' in j) and ('result' in j['upload']) and (j['upload']['result'] == 'Success'):
			print("Upload successful")
			return True
		else:
			print("Failed to upload file")
			self.failed_pages.append(filename)
			return False
			
	def importXML(self, xmldata, failcount=3, fullhistory=True):
		data = { 'format' : 'json', 'action' : 'import', 'token' : self.tokens["importtoken"] }
		if fullhistory:
			data['fullhistory'] = 'yes'
		r = requests.post(self.url, params=data, cookies=self.cookies, files={ 'xml' : ('input.xml', xmldata)})
		j = r.json()
		if 'import' in j and 'revisions' in j['import'][0]:
			print("Imported XML")
			return True
		else:
			print("Failed to import XML")
			if failcount > 0:
				# retry by recursing a certain number of times:
				if self.importXML(xmldata, failcount - 1, fullhistory) == True:
					return True
			else:
				self.failed_pages.append(xmldata)
				return False

# vim: ts=4 noet sw=4
