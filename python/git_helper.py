#!/usr/bin/python3

import os
from cmdtools import *
from pathlib import Path

class GitHelper(object):

	def __init__(self, module, root, quiet=False):
		self.module = module
		self.root = root
		self.quiet = quiet

	def localBranches(self):
		if os.path.exists(self.root):
			t1 = Task()
			retval, out = run_statusoutput("git -C %s for-each-ref --format=\"(refname)\" refs/heads")
			if retval == 0:
				for ref in out.split():
					yield ref.split("/")[-1]

	def localBranchExists(self, branch):
		return not run("git -C %s show-ref --verify --quiet refs/heads/%s" % (self.root, branch), quiet=self.quiet)

	def isReadOnly(self):
		try:
			Path(self.root + "/foo").touch()
		except (FileNotFoundError, PermissionError):
			return True
		else:
			os.unlink(self.root + "/foo")
			return False

	def readOnlyCheck(self):
		if self.isReadOnly():
			self.module.fatal("Repository is at %s is read-only. Cannot update." % self.root)

	def fetchRemote(self, branch, remote="origin"):
		self.readOnlyCheck()
		run("git -C %s remote set-branches --add %s %s" % (self.root, remote, branch), quiet=self.quiet)
		return run("git -C %s fetch %s refs/heads/%s:refs/remotes/%s/%s" % (self.root, remote, branch, remote, branch), quiet=self.quiet)

	def shallowClone(self, url, branch, depth=1):
		return run("git -C %s clone -b %s --depth=%s --single-branch %s" % (os.path.dirname(self.root), branch, depth, url), quiet=self.quiet)

	def pull(self, options=[]):
		self.readOnlyCheck()
		opts = " ".join(options)
		return run("git -C %s pull %s" % (self.root, opts), quiet=self.quiet)

	def reset(self, options=[]):
		self.readOnlyCheck()
		opts = " ".join(options)
		return run("git -C %s reset %s" % (self.root, opts), quiet=self.quiet)

	def clean(self, options=[]):
		self.readOnlyCheck()
		opts = " ".join(options)
		return run("git -C %s clean %s" % (self.root, opts), quiet=self.quiet)

	def exists(self):
		return os.path.exists(self.root)

	def isGitRepo(self):
		return os.path.exists(os.path.join(self.root, ".git"))

	def checkout(self, branch="master", origin=None):
		if origin is not None:
			args = "%s %s" % (origin, branch)
		else:
			args = branch
		retval = run("git -C %s checkout %s" % (self.root, args), quiet=self.quiet)
		return retval == 0

	@property
	def commitID(self):
		retval, out = run_statusoutput("git -C %s rev-parse HEAD" % self.root)
		if retval == 0:
			return out.strip()
		else:
			return None
