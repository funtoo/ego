=========
ego query
=========

---------------------------------------------
Funtoo Linux Ego Query Module
---------------------------------------------

:Author: Antoine Pinsard <antoine.pinsard@gmail.com>
:Version: ##VERSION##
:Manual section: 1
:Manual group: Funtoo Linux Core System

SYNOPSIS
========

The ``ego query`` is a tool to display information about packages. Bellow are described the various available commands.

``ego query [-h] [--version] [--verbosity VERBOSITY | -v | -q] {versions,v,origin,o,bugs} ...``

``ego query versions <atom>``

``ego query origin <package>``

``ego query bugs <package>``


QUERY VERSIONS
==============

The ``versions`` (shortcut: ``v``) command lists all available versions matching a given atom.
For each version, it also shows its slot and repository (along with git branch if any).::

 $ ego query versions python
  dev-lang/python|     slot|                 repo
 ----------------+---------+---------------------
           2.7.12|      2.7| python-kit/3.6-prime
         * 2.7.13|         | python-kit/3.6-prime
 ----------------+---------+---------------------
            3.4.5| 3.4/3.4m| python-kit/3.6-prime
            3.4.6|         | python-kit/3.6-prime
 ----------------+---------+---------------------
          * 3.5.3| 3.5/3.5m| python-kit/3.6-prime
 ----------------+---------+---------------------
       * 3.6.1-r1| 3.6/3.6m| python-kit/3.6-prime

 $ ego query versions '=python-3*'
  dev-lang/python|     slot|                 repo
 ----------------+---------+---------------------
            3.4.5| 3.4/3.4m| python-kit/3.6-prime
            3.4.6|         | python-kit/3.6-prime
 ----------------+---------+---------------------
          * 3.5.3| 3.5/3.5m| python-kit/3.6-prime
 ----------------+---------+---------------------
       * 3.6.1-r1| 3.6/3.6m| python-kit/3.6-prime

 $ ego query v dev-lang/python:3.5
  dev-lang/python|     slot|                 repo
 ----------------+---------+---------------------
          * 3.5.3| 3.5/3.5m| python-kit/3.6-prime

 $ ego query v coffee-script
  dev-lang/coffee-script| slot|           repo
 -----------------------+-----+---------------
                1.9.3-r1|    0| dev-kit/master
                * 1.12.5|     | dev-kit/master

  dev-ruby/coffee-script| slot|           repo
 -----------------------+-----+---------------
                   2.4.1|    0| dev-kit/master

Installed versions are in bold and marked with a star.


QUERY_ORIGIN
============

The ``origin`` (shortcut: ``o``) command will tell you where a given package comes from and give
you the URL to browse the ebuilds. This is mainly a tool for developers designed to figure out
where fixes should be applied.::

 $ ego query origin dev-python/appi
 dev-python/appi::python-kit comes from flora
         https://github.com/funtoo/flora/tree/master/dev-python/appi
 $ ego query o screen
 app-misc/screen::core-kit comes from kit-fixups
         https://github.com/funtoo/kit-fixups/tree/master/core-kit/global/app-misc/screen
         https://gitweb.gentoo.org/repo/gentoo.git/tree/app-misc/screen
 app-vim/screen::editors-kit comes from gentoo-staging
         http://git.funtoo.org/gentoo-staging/tree/app-vim/screen
         https://gitweb.gentoo.org/repo/gentoo.git/tree/app-vim/screen

When the package is also available in Gentoo, the URL to the Gentoo repository is also shown in
cyan as you may want to compare Funtoo version with Gentoo's.


QUERY BUGS
==========

The ``bugs`` command lists bugs reported on https://bugs.funtoo.org/ regarding the given atom.
This allows you to quickly find out if an issue you're facing was reported recently.::

 $ ego query bugs www-client/chromium
 FL-4233 2017-09-21 Closed Unable to emerge the package 'www-client/chromium' due to a missing dependency
 FL-3019 2015-11-27 Closed Emerge fails to find proper dependencies for www-client/chromium on arm with system-ffmpeg
 FL-444  2013-03-05 Closed www-client/chromium depends on missing >=media-libs/mesa-9.1
 $ ego query bugs mesa
 FL-3269 2016-07-19 Backlog media-libs/mesa need video_cards_virgl use flag.
 FL-2225 2015-03-29 Closed  [media-libs/mesa] upgrading to 10.4.4 failed
 FL-2224 2015-03-29 Closed  [media-libs/mesa] bump new 10.4.4 version to 10.4.7
 FL-634  2013-07-22 Closed  portage complaining that media-libs/mesa and x11-libs/cairo need openvg flag


ADDITIONAL DOCUMENTATION
========================

Please see http://www.funtoo.org/Package:Ego (``edoc "Package:Ego" | less``) for more detailed documentation.
