#!/usr/bin/python3

import sys
import unittest
sys.path.insert(0, "..")
from ego_profile import ProfileCatalog, ProfileTree, ProfileType, ProfileSpecifier
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

	def test_change_flavor(self):
		# can we grab the flavor? and is it the correct one?
		flav_list = list(self.pt.get_children(child_types=[ProfileType.FLAVOR]))
		self.assertEqual(len(flav_list), 1)
		self.assertEqual(flav_list[0].spec_str, 'core-kit:funtoo/1.0/linux-gnu/flavor/desktop')
		self.pt.replace_entry(ProfileType.FLAVOR, 'core-kit:funtoo/1.0/linux-gnu/flavor/core')
		flav_list = list(self.pt.get_children(child_types=[ProfileType.FLAVOR]))
		self.assertEqual(len(flav_list), 1)
		self.assertEqual(flav_list[0].spec_str, 'core-kit:funtoo/1.0/linux-gnu/flavor/core')

if __name__ == "__main__":
	unittest.main()

