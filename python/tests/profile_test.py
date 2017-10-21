#!/usr/bin/python3

import sys
import unittest
sys.path.insert(0, "..")
from profile import *
import os

class ProfileTest(unittest.TestCase):

	def setUp(self):

		# In the same directory as this test is a directory called 'profiles'. We set this up to be our fake profiles
		# directory, and also pretend the cwd is core-kit, so our fake 'core-kit' has a 'profiles' directory in it.
		# and we also have a file called 'parent' in the 'profiles' directory that we use to be our fake
		# /etc/portage/make.profile/parent.

		filedir = os.path.dirname(os.path.abspath(__file__))
		self.pc = ProfileCatalog(os.path.normpath(os.path.join(filedir, "profiles")))
		self.pt = ProfileTree(self.pc, "core-kit", { "core-kit" :filedir}, root_parent_dir="profiles")

	def test_basic(self):
		# can we grab the flavor? and is it the correct one?
		flav_list = list(self.pt.get_children(child_types=[ProfileType.FLAVOR]))
		self.assertEqual(len(flav_list), 1)
		self.assertEqual(flav_list[0].specifier, 'core-kit:funtoo/1.0/linux-gnu/flavor/desktop')

	def test_basic_recurse(self):
		# can we recursively grab all mix-ins inherited in the profile?
		mixin_list = list(self.pt.recursively_get_children(child_types=[ProfileType.MIX_IN]))
		self.assertEqual(len(mixin_list), 14)

if __name__ == "__main__":
	unittest.main()
