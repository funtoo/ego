========
ego sync
========

---------------------------------------------
Funtoo Linux Sync Module
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: ##VERSION##
:Manual section: 8
:Manual group: Funtoo Linux Core System

SYNOPSIS
========

``ego sync [-h] [--kits-only|--meta-repo-only|--in-place|--config-only] [--dest DESTINATION]``

USAGE
=====

Use the ``ego sync`` command to perform an initial clone of meta-repo, or to update meta-repo according to the settings
in ``/etc/ego.conf`` See ego.conf(5) for information on how to configure ``ego sync``.

``ego sync`` is typically run as the root user, but can also be run as a regular user. When run as a root user, the
code will look at the user and group ownership of the meta-repo directory if it exists and will 'drop permissions'
to run the sync operations as this user. If meta-repo does not yet exist, it will perform the sync operations as the
``portage`` user and the ``portage`` group.

When run as a regular user, ``ego sync`` will of course not drop permissions, but will perform sync operations as
the current user and the current user's primary group.

``ego sync``, when run as root, will run ``emerge sync`` in order to sync any non-Funtoo kits, and this will also
trigger any 'package move updates' (renames) that need to be applied to the package database in ``/var/db/pkg``.
When run as a regular user, these steps are skipped.

Syncing Kits Only
~~~~~~~~~~~~~~~~~

Use the ``--kits-only`` option to tell ego to only sync the kits themselves, and not update meta-repo.

Syncing Meta-Repo Only
~~~~~~~~~~~~~~~~~~~~~~
Use the ``--meta-repo-only`` option to tell ego to only sync meta-repo, and not update or clone any kits.

Syncing In-Place
~~~~~~~~~~~~~~~~
Use the ``--in-place`` option to tell ego to not perform any syncing, but to check out the correct kits according
to ``/etc/ego.conf`` kit and release settings, update ``/etc/portage/repos.conf``, and update the active profiles
accordingly. This is useful in conjunction when doing development and using Funtoo's merge-all-kits script to
generate your own local meta-repo. After this is done, moving to symlinking it to ``/var/git/meta-repo`` and running
``ego sync --in-place`` will ensure that the correct kit branches are checked out and that meta-repo is ready to use.
You must run ``ego sync --in-place`` as root since it must modify files in ``/etc/portage``.

Updating Config Only
~~~~~~~~~~~~~~~~~~~~
The ``--config-only`` option will instruct ego to not change the current kit branches that are checked out at all,
so ``meta-repo`` will not be touched, but the configuration in ``/etc/portage`` will be updated to reflect the current
state of ``meta-repo``. This is different than ``--in-place`` as what is in ``/etc/ego.conf`` is not consulted and
the files in ``/etc/portage`` are set up to use the ``meta-repo`` as it currently exists on disk. This is used by
``metro`` when building stages. When a meta-repo snapshot is extracted, ``ego sync --kits-only`` is run to grab the
kit repos, and then ``ego sync --config-only`` is run to update the files in ``/etc/portage`` to use this extracted
meta-repo.

Creating a Meta-Repo For Archiving
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``--dest`` option can be used to manually specify the location to point to a new location to create
a meta-repo. This setting overrides the ``meta_repo_path`` and ``kits_path`` settings in ``/etc/ego.conf``, and also
turns off automatic regeneration of repository configuration in ``/etc/portage/repos.conf``, as well as updates to
profile settings. This functionality is useful for creating a meta-repo for archiving purposes.


