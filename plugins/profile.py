#!/usr/bin/python3

import os
import argparse
import json

from ego.module import EgoModule
from ego.output import Color, Output, depluralize
from ego.profile import getProfileCatalogAndTree, ProfileType


class MultiChoicesAction(argparse.Action):
	def __init__(self, *args, **kwargs):
		self.multi_choices = kwargs.pop("choices")
		return super().__init__(*args, **kwargs)

	def __call__(self, parser, namespace, values, option_string=None):
		for value in values:
			if value not in self.multi_choices:
				raise argparse.ArgumentError(
					self, "invalid choice: %r (choose from %s)" % (value, ", ".join([repr(c) for c in self.multi_choices]))
				)
		setattr(namespace, self.dest, values)


class Module(EgoModule):
	def add_arguments(self, parser):

		# specify "mix-in" as alternate spelling for "mix-ins":

		valid_profile_types = [str(x) for x in ProfileType.valid()]
		subparsers = parser.add_subparsers(title="actions", dest="action")

		show_parser = subparsers.add_parser("show", help="Print profiles")
		show_parser.set_defaults(handler=self.handle_show_action)

		show_json_parser = subparsers.add_parser("show-json", help="Print profiles in JSON format")
		show_json_parser.set_defaults(handler=self.handle_show_json_action)

		get_parser = subparsers.add_parser("get", help="Print the value of a given profile")
		get_parser.add_argument("profile", choices=valid_profile_types)
		get_parser.set_defaults(handler=self.handle_get_action)

		list_parser = subparsers.add_parser("list", help="List given profiles (or all by default)")
		list_parser.add_argument(
			"profiles",
			nargs="*",
			choices=valid_profile_types,
			action=MultiChoicesAction,
			help=("Profiles to show: %s" % ", ".join(valid_profile_types)),
		)
		list_parser.set_defaults(handler=self.handle_list_action)

		update_parser = subparsers.add_parser("update", help="Update profiles (/etc/portage/make.profile/parent)")
		update_parser.set_defaults(handler=self.handle_write)

		single_profile_parsers = [
			subparsers.add_parser("arch", help="Change your arch profile"),
			subparsers.add_parser("build", help="Change your build profile"),
			subparsers.add_parser("subarch", help="Change your subarch profile"),
			subparsers.add_parser("flavor", help="Change your flavor profile"),
		]
		for subparser in single_profile_parsers:
			subparser.add_argument("new_value")
			subparser.set_defaults(handler=self.handle_single_profile_actions)

		mixins_parser = subparsers.add_parser("mix-ins", aliases=["mix-in"], help="Change your mix-ins profile")
		mixins_parser.add_argument("mixins", nargs="*")
		mixins_parser.set_defaults(handler=self.handle_mix_ins_action)

	def python_info(self):
		Output.header("Python kit")
		branch, default_branch = self.config.get_configured_kit("modules-kit")
		Output.log("%s%12s%s: %s%s%s" % (Color.BOLD, "branch", Color.END, Color.CYAN, branch, Color.END))

	def short_list(self):
		Output.header("Enabled Profiles")
		for key in [ProfileType.ARCH, ProfileType.BUILD, ProfileType.SUBARCH, ProfileType.FLAVOR, ProfileType.MIX_IN]:
			all_enabled = list(self.tree.get_children(key))
			if len(all_enabled) == 0:
				Output.log("%s%12s%s: (not set)" % (Color.BOLD, key, Color.END))
			else:
				for item in all_enabled:
					Output.log("%s%12s%s: %s%s%s" % (Color.BOLD, key, Color.END, Color.CYAN, item.name, Color.END))
		Output.log("")

	def short_JSON(self):
		outdict = {}
		for p_type in [ProfileType.ARCH, ProfileType.BUILD, ProfileType.SUBARCH, ProfileType.FLAVOR, ProfileType.MIX_IN]:
			key = str(p_type)
			outdict[key] = []
			for item in self.tree.get_children(p_type):
				out = {}
				out["shortname"] = item.name
				# if item.path is not None:
				# TODO: support path
				# 	out["path"] = item.path
				outdict[key].append(out)
		return outdict

	def handle_show_action(self):
		self.short_list()
		if not self.config.metadata_exists():
			self._no_repo_available()
		else:
			self.python_info()

		for specifier in self.tree.get_children([ProfileType.FLAVOR, ProfileType.MIX_IN]):

			for list_type in [ProfileType.FLAVOR, ProfileType.MIX_IN]:
				inherited_things = list(self.tree.recursively_get_children(list_type, specifier=specifier))

				if not len(inherited_things):
					continue

				Output.header("All inherited %s from %s %s" % (str(list_type), specifier.name, str(specifier.classify())))

				for inherited_spec in inherited_things:
					parent = self.tree.get_parent(inherited_spec)
					parent_name = parent.name if parent else "master profile"
					parent_type = depluralize(str(parent.classify())) if parent else "(None)"
					Output.log("      %s%26s%s (from %s %s)" % (Color.CYAN, inherited_spec.name, Color.END, parent_name, parent_type))
		Output.log("")

	def handle_write(self):
		Output.log(Color.bold("Updating profiles at %s..." % self.tree.master_parent_file))
		outdir = os.path.dirname(self.tree.master_parent_file)
		if not os.path.exists(outdir):
			Output.log(Color.bold("%s does not exist; creating..." % outdir))
			os.makedirs(outdir)
		try:
			with open(self.tree.master_parent_file, "w") as outfile:
				self.tree.write(self.config, outfile)
		except PermissionError:
			Output.fatal("You do not have permission to update profiles. Any changes could not be saved.")

	def handle_show_json_action(self):
		Output.log(json.dumps(self.short_JSON(), indent=4))

	def handle_get_action(self):
		Output.log(" ".join(p.name for p in self.tree.get_children(ProfileType.from_string(self.options.profile))))

	def handle_list_action(self):

		# Time to list all available profile settings.
		profiles = self.options.profiles

		for key in [ProfileType.ARCH, ProfileType.BUILD, ProfileType.SUBARCH, ProfileType.FLAVOR, ProfileType.MIX_IN]:
			if profiles and str(key) not in profiles:
				continue

			# active_keys: Names of active (currently enabled explicitly by user) profile keys
			# of this type (ie. flavor, etc.). These active ones will get highlighted differently.

			active_keys = [x.name for x in self.tree.get_children(key)]

			# get specifier.name, which is a property that is the last part of the profile path:
			recursively_active_keys = set(x.name for x in self.tree.recursively_get_children(key))
			available_keys = sorted(list(self.catalog.list(key)), key=lambda x: x.split(":")[-1])
			Output.header(str(key))

			# We handle our own output formatting/spacing/newlines. These vars are used for this.
			# lpos - column position; maxpos - when to wrap; count - item count.

			lpos = 4
			maxpos = 60
			count = 0

			# write each item out -- when we cross maxpos characters, add a newline and indent:
			Output.echo(" " * lpos)
			if not len(available_keys):
				Output.echo("None available")
				continue
			for x in available_keys:
				if lpos > maxpos:
					Output.echo("\n")
					lpos = 4
					Output.echo(" " * lpos)
				if x in active_keys:
					# make it stand out if it explicitly enabled:
					outx = Color.BOLD + Color.CYAN + x + "*" + Color.END
					if key in ["arch", "build"]:
						# parens to mark as read-only -- USE style. Not really read-only but should
						# not generally be changed by user.
						outx = "(" + outx + ")"
				elif x in recursively_active_keys:
					# highlight if enabled through inheritance:
					outx = Color.DARKCYAN + x + Color.END
				elif ":" in x:
					outx = Color.UNDERLINE + x + Color.END
				else:
					outx = x
				count += 1
				if count == 1 or lpos == 4:
					Output.echo(outx)
					lpos += len(x)
				else:
					Output.echo(", " + outx)
					lpos += len(x) + 2
			Output.log("")
		Output.log("")

	def handle_single_profile_actions(self):
		action = self.options.action
		newset = self.options.new_value
		profile_type = ProfileType.from_string(action)
		if profile_type is None:
			Output.fatal("Unknown profile type: %s" % action)
		elif profile_type == ProfileType.OTHER:
			Output.fatal("Profile type of 'other' not valid.")

		available_shortnames = set(self.catalog.list(profile_type))
		current_settings = list(self.tree.get_children(profile_type))
		if len(current_settings):
			current_setting = current_settings[0]
		else:
			current_setting = None
		if profile_type in [ProfileType.BUILD, ProfileType.ARCH]:
			if newset in available_shortnames and len(action) > 0:
				Output.warning(
					"Previous value: %s -- typically, user should not change this." % current_setting.name
					if current_setting is not None
					else None
				)

		if newset not in available_shortnames:
			Output.fatal(
				"%s %s is not available. Can't set. Available names: %s" % (action, newset, repr(available_shortnames))
			)
		self.writeout = True
		profile_path = self.catalog.find_path(profile_type, newset)
		if profile_path is None:
			Output.fatal("Could not find profile path for %s." % newset)
		self.tree.insert_or_replace_entry(profile_type, profile_path)

		self.short_list()
		Output.log(">>> Set %s to %s." % (action, newset))

	def handle_mix_ins_action(self):
		mixins = self.options.mixins

		adds = set()
		subs = set()
		for mixin in mixins:
			if mixin[0] == "-":
				subs.add(mixin[1:])
			elif mixin[0] == "+":
				adds.add(mixin[1:])
			else:
				adds.add(mixin)

		valids = list(self.catalog.list(ProfileType.MIX_IN))

		for mixin in adds.union(subs):
			if mixin not in valids:
				Output.fatal("Error: %s is not a valid mix-in." % mixin)

		# remove "-" arguments.
		removed = set()
		added = set()

		# for mix_in in enabled-mix-ins:

		enabled_mix_ins = list(self.tree.get_children([ProfileType.MIX_IN]))
		for mix_in in enabled_mix_ins:
			if mix_in.name in subs:
				removed.add(mix_in.name)
				self.tree.remove_name(ProfileType.MIX_IN, mix_in.name)
				self.writeout = True

		available_mix_in_shortnames = set(self.catalog.list(ProfileType.MIX_IN))
		not_added = adds - available_mix_in_shortnames

		for shortname in adds & available_mix_in_shortnames:
			profile_path = self.catalog.find_path(ProfileType.MIX_IN, shortname)
			if profile_path is None:
				Output.fatal("Could not find profile path for mix-in %s." % shortname)
			self.tree.append_mixin(profile_path)
			self.writeout = True

		# Do all output here -- our shortList() will reflect the mix-in changes made above. Then put informational messages
		# underneath for readability:

		self.short_list()
		for mixin in subs.difference(removed):
			Output.warning("Mix-in %s not found, not removing." % mixin)
		for mixin in not_added:
			Output.warning("Mix-in %s already active, not adding." % mixin)
		for mixin in removed:
			Output.log(">>> Removed %s mix-in." % mixin)
		for mixin in added:
			Output.log(">>> Added %s mix-in." % mixin)

	def handle(self):
		self.catalog, self.tree = getProfileCatalogAndTree(self.config)

		# If the profile needs to be written out for any reason, to either update it or fix it, writeout will be set to
		# true.

		self.writeout = self.tree.modified

		handler = getattr(self.options, "handler", self.handle_show_action)
		handler()

		for profile_type in ProfileType.single():
			settings = list(self.tree.get_children(profile_type))
			if len(settings) > 1:
				for setting in settings[1:]:
					Output.warning("Extra profile of type '%s' defined: '%s'. Will be removed." % (str(profile_type), setting.name))
				self.writeout = True
			elif len(settings) == 0:
				Output.warning("No %s defined. Please set." % str(profile_type))

		if self.writeout:
			self.handle_write()

	def __call__(self, *args):
		# Little trick to force end of arguments when using mix-ins command to
		# prevent argparse from considering "-foo" as an argument.
		if len(args) and "--" not in args and args[0] in ["mix-in", "mix-ins"]:
			args = (args[0], "--") + args[1:]
		super().__call__(*args)


# vim: ts=4 noexpandtab sw=4
