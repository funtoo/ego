import argparse
import sys

import appi

from ego_helpers import color

__all__ = ['EgoModule']


class EgoModule:

	verbosity = 1

	def debug(self, message):
		if self.verbosity > 1:
			sys.stdout.write(str(message) + '\n')
		sys.stdout.flush()

	def log(self, message):
		if self.verbosity > 0:
			sys.stdout.write(str(message) + '\n')
		sys.stdout.flush()

	def echo(self, message):
		if self.verbosity > 0:
			sys.stdout.write(str(message))
		sys.stdout.flush()

	def warning(self, message):
		if self.verbosity > -1:
			sys.stdout.write(color.yellow(str(message)) + '\n')
		sys.stdout.flush()

	def error(self, message):
		if self.verbosity > -1:
			sys.stderr.write(color.red(str(message)) + '\n')
		sys.stderr.flush()

	def fatal(self, message):
		self.error(message)
		sys.exit(1)

	def __init__(self, name, install_path, config):
		self.name = name
		self.install_path = install_path
		self.config = config

	def __call__(self, *args):
		parser = argparse.ArgumentParser('ego ' + self.name, description=self.help)
		parser.add_argument('--verbosity', default=1, type=int)
		self.add_arguments(parser)
		options = vars(parser.parse_args(args))
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
