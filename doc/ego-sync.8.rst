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

``ego sync [-h] [--kits-only] [--dest DESTINATION]``

USAGE
=====

Use the ``ego sync`` command to perform an initial clone of meta-repo, or to update meta-repo according to the settings
in ``/etc/ego.conf`` See ego.conf(5) for information on how to configure ``ego sync``.

Syncing Kits Only
~~~~~~~~~~~~~~~~~

Use the ``--kits-only`` option to tell ego to only sync the kits themselves, and not update meta-repo.

Creating a Meta-Repo For Archiving
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``--dest`` option can be used to manually specify the location to point to a new location to create
a meta-repo. This setting overrides the ``meta_repo_path`` and ``kits_path`` settings in ``/etc/ego.conf``, and also
turns off automatic regeneration of repository configuration in ``/etc/portage/repos.conf``, as well as updates to
profile settings. This functionality is useful for creating a meta-repo for archiving purposes.


