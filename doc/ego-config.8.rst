==========
ego config
==========

---------------------------------------------
Funtoo Linux Configuration Module
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: ##VERSION##
:Manual section: 1
:Manual group: Funtoo Linux Core System

SYNOPSIS
========

The ``ego config`` command allows for easy querying and setting of values in ``/etc/ego.conf`` from the command-line.

``ego config get [section] [key]``

``ego config set [section] [key] [value]``

EXAMPLES
========

Here are some examples of use::

 # ego config get kits python-kit
 3.6-prime

 # ego config set kits python-kit 3.7-prime

 === Changing setting kits/python-kit: ===

 Old value: 3.6-prime
 New value: 3.7-prime

 Setting saved to /etc/ego.conf.
