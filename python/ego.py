import argparse
import json
from collections import OrderedDict
from pathlib import Path
import sys

from ego_helpers import Color

__all__ = ['EgoModule']


class EgoModule:

	verbosity = 1

	# I think it is time to add a "news" or "issues" functionality to Ego Modules, which would allow an ego
	# module to register information that would be presented to the user, even at a later invocation of ego.
	# I plan to use this to implement the ability to have "post-kit-change" actions, which can be performed
	# potentially automatically or manually, after a user has changed a kit. And potentially we need pre-
	# change actions too.

	# I would also like to add a mechanism to 'remember' warnings, etc so they could be repeated at the end
	# of ego, to remind users. For example, I could use this to remind a user that they are referencing a
	# kit that doesn't exist in ego.conf, and that they should fix it, cleanly and at the end of ego output.

	def _output(self, message, err=False):
		message = str(message)
		if not message.endswith('\n'):
			message += '\n'
		out = sys.stderr if err else sys.stdout
		out.write(message)
		out.flush()

	def debug(self, message):
		"""Output debug message to stdout. Auto-append newline if missing"""
		if self.verbosity > 1:
			self._output(message)

	def log(self, message):
		"""Output message to stdout. Auto-append newline if missing."""
		if self.verbosity > 0:
			self._output(message)

	def echo(self, message):
		"""Output message as-is to stdout."""
		if self.verbosity > 0:
			sys.stdout.write(str(message))
			sys.stdout.flush()

	def warning(self, message):
		"""Output warning message to stdout. Auto-append newline if missing."""
		if self.verbosity > -1:
			self._output(Color.yellow(str(message)))

	def error(self, message):
		"""Output error message to stderr. Auto-append newline if missing."""
		if self.verbosity > -1:
			self._output(Color.red(str(message)), err=True)

	def fatal(self, message, exit_code=1):
		"""Output error message to stderr and exit. Auto-append newline if missing."""
		self.error(message)
		sys.exit(exit_code)

	def load_kit_metadata(self, fn):
		if not hasattr(self, '_kit_%s' % fn):
			path = Path(self.config.meta_repo_root) / 'metadata' / ('kit-%s.json' % fn)
			try:
				with path.open() as f:
					return json.loads(f.read(), object_pairs_hook=OrderedDict)
			except OSError:
				return {}
		return getattr(self, '_kit_%s' % fn)

	@property
	def kit_info(self):
		return self.load_kit_metadata('info')

	@property
	def kit_sha1(self):
		return self.load_kit_metadata('sha1')

	def get_selected_kit(self, kit, show_default=False):
		if "kits" in self.config.settings and kit in self.config.settings["kits"]:
			branch = self.config.settings["kits"][kit]
		else:
			branch = None
		if branch and not show_default:
			return branch
		default = self.kit_info["kit_settings"][kit]["default"]
		if show_default:
			return (branch, default)
		else:
			return default

	def setup(self):
		# Easy method for modules to perform constructor-related things.
		pass

	def __init__(self, name, install_path, config):
		self.name = name
		self.install_path = install_path
		self.config = config
		self.info = config.ego_mods_info[name]
		self.setup()

	def __call__(self, *args):
		parser = argparse.ArgumentParser('ego ' + self.name, description=self.info['description'])
		parser.add_argument('--version', action='version', version=(
			"ego %(ego_version)s / %(module)s %(module_version)s (by %(module_author)s)" % {
				'ego_version': self.config.ego_version, 'module': self.name,
				'module_version': self.info['version'], 'module_author': self.info['author'],
			}
		))
		verbosity_group = parser.add_mutually_exclusive_group()
		verbosity_group.add_argument('--verbosity', default=1, type=int, help="Set verbosity level")
		verbosity_group.add_argument('-v', default=0, action='count', help="Increase verbosity level by 1 per occurrence")
		verbosity_group.add_argument('-q', default=0, action='count', help="Decrease verbosity level by 1 per occurrence")
		self.add_arguments(parser)
		options = parser.parse_args(args)
		options = vars(options)
		self.verbosity = options.pop('verbosity') + options.pop('v') - options.pop('q')
		self.handle(**options)

	def add_arguments(self, parser):
		pass

	def handle(self, **options):
		raise NotImplementedError

	@staticmethod
	def atom_argument(strict=True):
		import appi  # Import appi here to avoid hard dependency of all modules to appi

		def atom_type(value):
			try:
				return appi.QueryAtom(value, strict)
			except appi.AtomError as e:
				raise argparse.ArgumentTypeError(str(e))
		return atom_type

# vim: ts=4 sw=4 noexpandtab
