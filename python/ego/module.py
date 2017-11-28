import argparse
import importlib.machinery
import sys
import os

from ego.output import Color, Output

__all__ = ['EgoModule', 'usage']

def usage(config):
	print("Usage: %s [module] [info|options]..." % os.path.basename(sys.argv[0]))
	Output.header("Available ego modules")
	for mod, info in config.available_modules():
		desc = ''
		if "description" in info:
			desc = info["description"]
		if "shortcut" in info:
			desc += " (%s%s%s)" % (Color.BOLD, info["shortcut"], Color.END)
		print("%s%15s%s - %s" % (Color.CYAN, mod, Color.END, desc))
	print()

class EgoModule:

	# I think it is time to add a "news" or "issues" functionality to Ego Modules, which would allow an ego
	# module to register information that would be presented to the user, even at a later invocation of ego.
	# I plan to use this to implement the ability to have "post-kit-change" actions, which can be performed
	# potentially automatically or manually, after a user has changed a kit. And potentially we need pre-
	# change actions too.

	# I would also like to add a mechanism to 'remember' warnings, etc so they could be repeated at the end
	# of ego, to remind users. For example, I could use this to remind a user that they are referencing a
	# kit that doesn't exist in ego.conf, and that they should fix it, cleanly and at the end of ego output.

	def setup(self):
		# Easy method for modules to perform constructor-related things.
		pass

	def __init__(self, name, config, VERSION=None):
		self.name = name
		self.config = config
		self.info = config.ego_mods_info[name]
		self.version = VERSION
		self.setup()

	def __call__(self, *args):
		parser = argparse.ArgumentParser('ego ' + self.name, description=self.info['description'])
		if self.version:
			parser.add_argument('--version', action='version', version=(
				"ego %(ego_version)s / %(module)s %(module_version)s (by %(module_author)s)" % {
					'ego_version': self.version, 'module': self.name,
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
		options["parser"] = parser
		Output.verbosity = options.pop('verbosity') + options.pop('v') - options.pop('q')
		self.handle(**options)

	def add_arguments(self, parser):
		pass

	def handle(self, **options):
		raise NotImplementedError

	@classmethod
	def run_ego_module(cls, modname, config, args, VERSION=None):
		loader = importlib.machinery.SourceFileLoader(modname, '%s/modules/%s.ego' % (config.ego_dir, modname))
		try:
			mod = loader.load_module()
			if mod:
				ego_module = mod.Module(modname, config, VERSION)
				ego_module(*args)
			else:
				print(Color.RED + "Error: ego module \"%s\" not found." % modname + Color.END)
				sys.exit(1)
		except FileNotFoundError:
			return None

# vim: ts=4 sw=4 noexpandtab