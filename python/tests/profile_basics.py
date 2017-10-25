#!/usr/bin/python3

import sys
import unittest
sys.path.insert(0, "..")
from ego_profile import *
import os

class ProfileTest(unittest.TestCase):

	def setUp(self):

		# In the same directory as this test is a directory called 'profiles'. We set this up to be our fake profiles
		# directory, and also pretend the cwd is core-kit, so our fake 'core-kit' has a 'profiles' directory in it.
		# and we also have a file called 'parent' in the 'profiles' directory that we use to be our fake
		# /etc/portage/make.profile/parent.

		filedir = os.path.dirname(os.path.abspath(__file__))
		self.mydir = os.path.normpath(os.path.join(filedir, "profiles"))
		self.pc = ProfileCatalog(self.mydir)
		self.pt = ProfileTree(self.pc, "core-kit", { "core-kit" :filedir}, root_parent_dir="profiles")

	def test_classify(self):
		ps = ProfileSpecifier(self.pt, self.mydir, 'funtoo/1.0/linux-gnu/flavor/core')
		self.assertEqual(ps.classify(), ProfileType.FLAVOR)

	def test_basic(self):
		# can we grab the flavor? and is it the correct one?
		flav_list = list(self.pt.get_children(child_types=[ProfileType.FLAVOR]))
		self.assertEqual(len(flav_list), 1)
		self.assertEqual(flav_list[0].spec_str, 'core-kit:funtoo/1.0/linux-gnu/flavor/desktop')

	def test_basic_recurse(self):
		# can we recursively grab all mix-ins inherited in the profile?
		mixin_list = list(self.pt.recursively_get_children(child_types=[ProfileType.MIX_IN]))
		self.assertEqual(len(mixin_list), 14)

	def test_mixin_list(self):
		mix_in_set = {'print', 'mediaformat-audio-extra', 'mediaformat-video-common', 'lxde',
		              'mediadevice-audio-consumer', 'dvd', 'mediaformat-gfx-common', 'selinux', 'gfxcard-intel-glamor',
		              'gnome', 'X', 'gnome-3.16-fixups', 'python3-only', 'mate', 'xfce', 'mediaformat-gfx-extra',
		              'no-systemd', 'mediadevice-audio-pro', 'kde', 'audio', 'no-emul-linux-x86', 'kde-plasma-5',
		              'hardened', 'media-pro', 'media', 'mediadevice-video-pro', 'mediaformat-audio-common', 'cinnamon',
		              'mediadevice-video-consumer', 'vmware-guest', 'mediadevice-base', 'mediaformat-video-extra',
		              'lxqt', 'console-extras', 'openvz-host'}
		mix_in_set_2 = set(self.pc.list(ProfileType.MIX_IN))
		self.assertEqual(mix_in_set, mix_in_set_2)
		mix_in_set_with_arch = {'print', 'mediaformat-audio-extra', 'mediaformat-video-common', 'lxde',
		                        'mediadevice-audio-consumer', 'dvd', 'mediaformat-gfx-common', 'selinux',
		                        'gfxcard-intel-glamor', 'gnome', 'X', 'gnome-3.16-fixups', 'python3-only', 'mate',
		                        'xfce', 'mediaformat-gfx-extra', 'no-systemd', 'mediadevice-audio-pro', 'kde', 'audio',
		                        'no-emul-linux-x86', 'kde-plasma-5', 'hardened', 'media-pro', 'media',
		                        'mediadevice-video-pro', 'mediaformat-audio-common', 'cinnamon',
		                        'mediadevice-video-consumer', 'vmware-guest', 'mediadevice-base',
		                        'mediaformat-video-extra', 'lxqt', 'console-extras', 'openvz-host'}
		mix_in_set_with_arch_2 = set(self.pc.list(ProfileType.MIX_IN, arch="x86-64bit"))
		self.assertEqual(mix_in_set_with_arch, mix_in_set_with_arch_2)

if __name__ == "__main__":
	unittest.main()
