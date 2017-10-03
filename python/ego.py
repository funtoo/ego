import argparse
import sys

from ego_helpers import color

__all__ = ['EgoModule']


class EgoModule:

	verbosity = 1

	def debug(self, message):
		if self.verbosity > 1:
			sys.stdout.write(message + '\n')

	def log(self, message):
		if self.verbosity > 0:
			sys.stdout.write(message + '\n')

	def warning(self, message):
		if self.verbosity > -1:
			sys.stdout.write(color.yellow(message) + '\n')

	def error(self, message):
		if self.verbosity > -1:
			sys.stderr.write(color.red(message) + '\n')

	def fatal(self, message):
		self.error(message)
		sys.exit(1)

	def __init__(self, install_path, config):
		self.install_path = install_path
		self.config = config

	def __call__(self, *args):
		parser = argparse.ArgumentParser(self.description)
		parser.add_argument('--verbosity', default=1, type=int)
		self.add_arguments(parser)
		options = parser.parse_args(args)
		self.verbosity = options['verbosity']
		self.handle(**options)

	def add_arguments(self, parser):
		pass

	def handle(self, **options):
		raise NotImplementedError

# vim: ts=4 sw=4 noexpandtab
