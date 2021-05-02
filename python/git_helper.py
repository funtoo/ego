#!/usr/bin/python3

import os
from cmdtools import run_statusoutput, run
from pathlib import Path
from datetime import datetime
from ego.output import Output


class GitHelper(object):
	def __init__(self, module, root, quiet=False):
		self.module = module
		self.root = root
		self.quiet = quiet

	def localBranches(self):
		if os.path.exists(self.root):
			retval, out = run_statusoutput('git -C %s for-each-ref --format="(refname)" refs/heads' % self.root)
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
			Output.fatal("Repository is at %s is read-only. Cannot update." % self.root)

	def fetchRemote(self, branch, remote="origin", options=None):
		options = options or []
		self.readOnlyCheck()
		opts = " ".join(options)
		run("git -C %s remote set-branches --add %s %s" % (self.root, remote, branch), quiet=self.quiet)
		return run(
			"git -C %s fetch %s %s refs/heads/%s:refs/remotes/%s/%s" % (self.root, opts, remote, branch, remote, branch),
			quiet=self.quiet,
		)

	def clone(self, url, branch, depth=None):
		if depth is not None:
			depth_str = "--depth=%s" % depth
		else:
			depth_str = ""
		return run("git clone -b %s %s --single-branch %s %s" % (branch, depth_str, url, self.root), quiet=self.quiet)

	def pull(self, options=None):
		options = options or []
		self.readOnlyCheck()
		opts = " ".join(options)
		return run("git -C %s pull %s --ff-only" % (self.root, opts), quiet=self.quiet)

	def reset(self, options=None):
		options = options or []
		self.readOnlyCheck()
		opts = " ".join(options)
		return run("git -C %s reset %s" % (self.root, opts), quiet=self.quiet)

	def clean(self, options=None):
		options = options or []
		self.readOnlyCheck()
		opts = " ".join(options)
		return run("git -C %s clean %s" % (self.root, opts), quiet=self.quiet)

	def exists(self):
		return os.path.exists(self.root)

	def is_git_repo(self):
		return os.path.exists(os.path.join(self.root, ".git"))

	def checkout(self, branch="master", origin=None):
		if origin is not None:
			args = "%s %s" % (origin, branch)
		else:
			args = branch
		retval = run("git -C %s checkout %s" % (self.root, args), quiet=self.quiet)
		return retval == 0

	def last_sync(self):
		"""Returns datetime of last sync, or None if not a git repo."""
		check_f = self.root + "/.git/FETCH_HEAD"
		try:
			return datetime.fromtimestamp(os.path.getmtime(check_f))
		except FileNotFoundError:
			return None

	@property
	def commitID(self):
		retval, out = run_statusoutput("git -C %s rev-parse HEAD" % self.root)
		if retval == 0:
			return out.strip()
		else:
			return None
