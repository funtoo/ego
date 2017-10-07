import argparse
import sys

import appi

from ego_helpers import color

__all__ = ['EgoModule']


class EgoModule:

	verbosity = 1

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
			self._output(color.yellow(str(message)))

	def error(self, message):
		"""Output error message to stderr. Auto-append newline if missing."""
		if self.verbosity > -1:
			self._output(color.red(str(message)), err=True)

	def fatal(self, message, exit_code=1):
		"""Output error message to stderr and exit. Auto-append newline if missing."""
		self.error(message)
		sys.exit(exit_code)

	def __init__(self, name, install_path, config):
		self.name = name
		self.install_path = install_path
		self.config = config

	def __call__(self, *args):
		parser = argparse.ArgumentParser('ego ' + self.name, description=self.help)
		parser.add_argument('--verbosity', default=1, type=int)
		self.add_arguments(parser)
		options = parser.parse_args(args)
		options = vars(options)
		self.verbosity = options['verbosity']
		self.handle(**options)

	def add_arguments(self, parser):
		pass

	def handle(self, **options):
		raise NotImplementedError

	@staticmethod
	def atom_argument(strict=True):
		def atom_type(value):
			try:
				return appi.QueryAtom(value, strict)
			except appi.AtomError as e:
				raise argparse.ArgumentTypeError(str(e))
		return atom_type

# vim: ts=4 sw=4 noexpandtab
