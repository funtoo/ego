=================
Ego Merge Actions
=================

The concept of 'merge actions' is that ego would have the ability to either:

1. Automatically perform certain system administration actions, or
2. Specify administration action steps that the user can perform manually

This functionality could be called something else, such as 'automated system management', 'system policy engine',
or something else.

Action Priorities
-----------------

These actions could have varying priority. One can imagine the following priorities:

1. Optional - something that could potentially be done, to inform the user.
2. Suggested - something that we would generally recommend be done.
3. Security - something that is security-related, which in turn could have its own sub-levels.
4. Required - something that is necessary to be done to maintain key system functionality.

In turn, users could then configure ego as to how each priority action should be handled. For example, a user could opt
to have all 'required' actions be performed automatically, be prompted to perform suggested actions, and to not perform
optional actions. This would likely be the default for ego.

Action Triggers
---------------

Action triggers refer to when a particular action should be invoked. The following are ideas:

1. ``pre-kit-branch-switch`` - prior to switching a kit branch, perform an action.
2. ``post-kit-branch-switch`` - after switching to a kit branch, perform an action.
3. ``pre-sync`` - prior to a sync operation. This can be performed by grabbing remote metadata prior to actually performing
   a git pull.
4. ``post-sync`` - after a sync operation.

Actions
-------

A number of actions could be performed, with more added in the future. These actions could include:

#. Switching the system python to a particular version -- for example, prior to switching Python kit, one should
   switch system python to 2.7 so that Portage continues to function. This should technically be done before a new
   python-3 is merged.

#. Ensuring that the most recent version of Portage or Ego is installed.

#. Performing necessary rebuilds of various packages, as needed, after a new kit has been enabled.

#. Simply logging that a particular package has a known vulnerability and should be upgraded -- or take care of
   upgrading it automatically.

The logging functionality could use a new "persistent logging engine" that will be added to ego to persistently record
issues that should be addressed, as well as news items.

References
----------

See the following bugs for issues that could be addressed with this functionality.

FL-4156: [ego-2] ego sync fails with ImportError
  https://bugs.funtoo.org/browse/FL-4156

FL-3812: ego systcl tuning - blobs
  https://bugs.funtoo.org/browse/FL-3812

FL-4289: ego: create actions
  https://bugs.funtoo.org/browse/FL-4289

FL-4131: When upgrades to core packages of funtoo exist - do them first and restart emerge
  https://bugs.funtoo.org/browse/FL-4131

FL-4065: Update Xorg from v1.17 to v1.19
  https://bugs.funtoo.org/browse/FL-4065