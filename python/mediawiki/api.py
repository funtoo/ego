#!/usr/bin/python3

import requests

# MediaWiki API Mark 3
#
# Copyright 2017 Daniel Robbins and Funtoo Solutions, Inc.
# See LICENSE.txt for terms of distribution. 

class Wiki(object):

	def __init__(self,url):

		self.url = url
		self.cookies = {}
		self.logged_in = False
		self.tokens = {}
		self.failed_pages = []

	# Use login2 with MediaWiki earlier than 1.27.

	def login2(self,user,password, lgtoken=None):
		data = { 'format' : 'json', 'action' : 'login', 'lgname' : user }
		body_data = { 'lgpassword' : password }
		if lgtoken is not None:
			body_data["lgtoken"] = lgtoken
		r = requests.post(self.url, params=data, data=body_data, cookies=self.cookies)
		j = r.json()
		if ('login' in j) and ('result' in j['login']):
			self.cookies = r.cookies
			print(j)
			if j['login']['result'] == "Success":
				print("Login successful")
				self.logged_in = True
			elif j['login']['result'] == "NeedToken":
				data['lgtoken'] = j['login']['token']
				r = requests.post(self.url, params=data, cookies=self.cookies)
				j = r.json()
				print(j)
				if j['login']['result'] == "Success":
					self.cookies.update(r.cookies)
					self.logged_in = True
			else:
				print("login failure", j)
		else:
			print("login failed: ", j)
		return self.logged_in

	# Use login with MediaWiki 1.27 or later.

	def login(self, user, password):
		data = { 'format' : 'json', 'action' : 'query' , 'meta' : 'tokens', 'type' : 'login' }
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		try:
			print(r.cookies)
			self.cookies.update(r.cookies)
			return self.login2(user, password, lgtoken=j['query']['tokens']['logintoken'])
		except KeyError:
			raise
			return False

	def show_cookies(self):
		return dict(self.cookies)

	def getTokens(self,kinds=["edit","import"]):
		if not self.logged_in:
			return False
		data = { 'format' : 'json', 'action' : 'tokens' , 'type' : '|'.join(kinds) }
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		print(j)
		if 'tokens' in j:
			self.tokens = j['tokens']
		return self.tokens

	def getAllPages(self, namespace=0, limit=10000, from_page=None, page_filter=None):
		data = { 'format' : 'json', 'action' : 'query', 'list' : 'allpages', 'apnamespace' : namespace, 'aplimit' : limit }
		if from_page is not None:
			data['apfrom'] = from_page
		if page_filter is not None:
			data['apfilterredir'] = page_filter
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'allpages' in j['query']:
			return j['query']['allpages']

	def getAllPagesInCategory(self, category, limit=500, cmcontinue=None):
		data = { 'format' : 'json', 'action' : 'query', 'cmtype' : 'page', 'list' : 'categorymembers', 'cmtitle': "Category:%s" % category, 'cmlimit' : limit }
		if cmcontinue is not None:
			data['cmcontinue'] = cmcontinue
		print(data)
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		print(j)
		if 'query' in j and 'categorymembers' in j['query']:
			if 'continue' in j and 'cmcontinue' in j['continue']:
				# there's more...
				return j['continue']['cmcontinue'], j['query']['categorymembers']
			else:
				# no more
				return None, j['query']['categorymembers']

	def getAllRedirectsToPage(self, page, rdcontinue=None):
		data = { 'format' : 'json', 'action' : 'query', 'prop' : 'redirects', 'titles': page, 'rdprop': 'title|fragment'}
		if rdcontinue is not None:
			data['rdcontinue'] = rdcontinue
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		print(j)
		if 'query' in j and 'pages' in j['query']:
			if 'continue' in j and 'rdcontinue' in j['continue']:
				# there's more...
				return j['continue']['rdcontinue'], j['query']
			else:
				# no more
				return None, j['query']
		return None, None

	def getRecentChanges(self, args={}):
		data = { 'format' : 'json', 'action' : 'query', 'list' : 'recentchanges' }
		data.update(args)
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'recentchanges' in j['query']:
			return j['query']['recentchanges']

	def getPage(self, title):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'revisions', 'rvprop' : 'content' }
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'pages' in j['query']:
			w = j['query']['pages']
			if 'revisions' in w[list(w.keys())[0]]:
				return w[list(w.keys())[0]]["revisions"][0]["*"]
		return None

	def putPage(self, title, content):
		if "edittoken" not in self.tokens:
			self.getTokens()
		if "edittoken" not in self.tokens:
			raise IndexError
		data = { 'format' : 'json', 'action' : 'edit', 'title' : title, 'text' : content, 'contentformat' : 'text/x-wiki', 'token' : self.tokens["edittoken"]}
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if 'edit' in j and 'result' in j['edit'] and j['edit']['result'] == 'Success':
			return True
		return False

	def importPage(self, title, interwiki, namespace=0, failcount=3):
		data = { 'format' : 'json', 'action' : 'import', 'interwikisource' : interwiki, 'interwikipage' : title, 'namespace' : namespace, 'fullhistory' : 'yes', 'token' : self.tokens["importtoken"] }
		r = requests.post(self.url, data=data, cookies=self.cookies)
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
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		return j

	def getImages(self, from_img=None):
		data = { 'format' : 'json', 'action' : 'query', 'list' : 'allimages', 'ailimit' : '1000' }
		if from_img is not None:
			data["aifrom"] = from_img
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if 'continue' in j:
			return j['continue']['aicontinue'], map(lambda x: x['name'], j['query']['allimages'])
		else:
			return None, map(lambda x: x['name'], j['query']['allimages'])

	def getPageImages(self, title):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'images' }
		data['imlimit'] = 1000
		r = requests.post(self.url, data=data, cookies=self.cookies)
		try:
			j = r.json()
		except json.decoder.JSONDecodeError:
			return []
		# TODO: ^^^^ maybe return None, detect when this call fails so we can re-attempt it
		if 'query' in j and 'pages' in j['query']:
			k = j['query']['pages'].keys()
			if len(k) == 1:
				i = j['query']['pages'][list(k)[0]]
				if 'images' in i:
					return i['images']
		return []

	def getImageURL(self, title):
		data = { 'format' : 'json', 'action' : 'query', 'titles' : title, 'prop' : 'imageinfo', 'iiprop' : 'url' }
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if 'query' in j and 'pages' in j['query']:
			k = j['query']['pages'].keys()
			if len(k) == 1:
				i = j['query']['pages'][list(k)[0]]
				if 'imageinfo' in i and 'url' in i['imageinfo'][0]:
					return i['imageinfo'][0]['url']
		return None

	def importPageImages(self, title, source_wiki, upload_log: set = None):
		if upload_log is None:
			upload_log = set()
		"specify a page -- find all image links and upload them into this wiki."
		print("Attempting to import page \"%s\" images..." % title)
		# Attempt to grab images referenced on this page -- even though they may not exist.
		images = source_wiki.getPageImages(title)
		for i in images:
			print("PROCESS IMG", i)
			if i["title"] in upload_log:
				print("Skipping %s, already uploaded or attempted" % i)
				continue
			upload_log.add(i["title"])
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

	def importPageAndImages(self, title, source_wiki, interwiki, namespace=0, failcount=3, upload_log=None):
		"specify a page -- import the page, and if successful, also transwiki all image links."
		result = self.importPage(title, interwiki, namespace, failcount)
		if result == True:
			self.importPageImages(title, source_wiki, interwiki, upload_log=upload_log)

	def exportXML(self, title):
		data = { 'format' : 'json', 'action': 'query' , 'titles' : title, 'export' : 'yes', 'exportnowrap' : 'yes' }
		r = requests.post(self.url, data=data, cookies=self.cookies)
		return r.text

	def uploadFileFromURL(self, filename, url):
		data = { 'format' : 'json', 'action' : 'upload', 'url' : url, 'filename' : filename, 'token' : self.tokens["edittoken"] }
		print("Uploading file %s from url %s to wiki %s" % (filename, url, self.url))
		r = requests.post(self.url, data=data, cookies=self.cookies)
		j = r.json()
		if ('upload' in j) and ('result' in j['upload']):
			if (j['upload']['result'] == 'Success'):
				return True, {}
			elif j['upload']['result'] == 'Warning':
				self.failed_pages.append(filename)
				return False, j['upload']['warnings']
		else:
			self.failed_pages.append(filename)
			return False, {}
			
	def importXML(self, xmldata, failcount=3, fullhistory=True):
		data = { 'format' : 'json', 'action' : 'import', 'token' : self.tokens["importtoken"] }
		if fullhistory:
			data['fullhistory'] = 'yes'
		r = requests.post(self.url, data=data, cookies=self.cookies, files={ 'xml' : ('input.xml', xmldata)})
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
