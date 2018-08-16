# -*- coding: ascii -*-
import os
import sys

def pytext(myfile, globals):
	"interprets a text file with embedded elements"

	# add os and sys modules to globals since we've already imported them

	globals["os"] = os
	globals["sys"] = sys

	try:
		a=open(myfile,'r')
	except IOError:
		sys.stderr.write("!!! Error opening "+myfile+"!\n")
		return
	mylines=a.readlines()
	a.close()
	pos=0
	while pos<len(mylines):
		if mylines[pos][0:8]=="<?python":
			mycode=""
			pos=pos+1
			while (pos<len(mylines)) and (mylines[pos][0:2]!="?>"):
				mycode=mycode+mylines[pos]
				pos=pos+1
			pos += 1
			exec mycode in globals
		else:
			sys.stdout.write(mylines[pos])
			pos=pos+1


