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

``ego sync [-h] [--kits|--no-kits] [--meta|--no-meta] [--in-place] [--config|--no-config] [--dest DESTINATION]``

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

Disable Updates to Kits
~~~~~~~~~~~~~~~~~~~~~~~

By default, all kits will be updated. To turn this off, specify the ``--no-kits`` option.

Disable Updates to Meta-Repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, meta-repo will be updated to the latest version available. To turn this off, specify the
``--no-meta`` option. This is used by metro when it is using a Portage snapshot and wants to use *that*
snapshot and not update it.

Disable Config Updates
~~~~~~~~~~~~~~~~~~~~~~

By default, ``ego sync`` will update configuration in ``/etc/portage``, unless ``--dest`` is being used
to write out the meta-repo to a non-default location. This involves ensuring that the correct kits are
checked out according to ``/etc/ego.conf`` kit and release settings, and that updates are made to
``/etc/portage/repos.conf``, and the active profiles enabled in ``/etc/portage/make.profile/parent``
are set correctly based on your profile (flavor and mix-in) settings.

You almost always want config to be updated when you run ``ego sync`` to ensure everything is
configured properly, but if you want to disable this, you can use the ``--no-config`` option
which will disable these configuration updates.


Syncing In-Place
~~~~~~~~~~~~~~~~
Use the ``--in-place`` option to tell ego to not perform any syncing, so it is short-hand for ``--no-meta --no-kits``.


Creating a Meta-Repo For Archiving
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``--dest`` option can be used to manually specify the location to point to a new location to create
a meta-repo. This setting overrides the ``meta_repo_path`` and ``kits_path`` settings in ``/etc/ego.conf``, and also
turns off automatic regeneration of repository configuration in ``/etc/portage/repos.conf``, as well as updates to
profile settings. This functionality is useful for creating a meta-repo for archiving purposes.


