#!/usr/bin/python3

import sys
import unittest

sys.path.insert(0, "..")
from ego.profile import ProfileType


class ProfileEnumTest(unittest.TestCase):
	def test_compare(self):
		self.assertGreater(ProfileType.BUILD, ProfileType.ARCH)
		self.assertGreater(ProfileType.SUBARCH, ProfileType.BUILD)
		self.assertGreater(ProfileType.FLAVOR, ProfileType.SUBARCH)
		self.assertGreater(ProfileType.MIX_IN, ProfileType.FLAVOR)
		self.assertGreater(ProfileType.MIX_IN, ProfileType.ARCH)

	def test_string_compare(self):
		self.assertEqual(ProfileType.ARCH, "arch")
		self.assertEqual(ProfileType.BUILD, "build")
		self.assertEqual(ProfileType.SUBARCH, "subarch")
		self.assertEqual(ProfileType.FLAVOR, "flavor")
		self.assertEqual(ProfileType.MIX_IN, "mix-ins")


if __name__ == "__main__":
	unittest.main()
