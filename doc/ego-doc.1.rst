=========
ego doc
=========

---------------------------------------------
Funtoo Linux Ego Documentation Module
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: ##VERSION##
:Manual section: 1
:Manual group: Funtoo Linux Core System

SYNOPSIS
========

The ``ego doc`` or ``edoc`` command can be used to render Funtoo Linux wiki documentation for console viewing. To use
this command, specify the name of the article as the first argument. It is recommended that you pipe the output of this
command to ``less`` or another pager so that you can scroll through the output.

FEATURES
========

When the following commands are run ``ego doc`` will query the MediaWiki API and retrieve the latest wikitext for the
specified page, and will then colorize and render the wikitext. The wikitext renderer includes the following features:

* Colorization
* Proper rendering of console output
* Proper rendering of tables
* Inclusion of clickable hyperlinks for URLs

Here are some examples of use::

  edoc Install | less
  edoc Networking | less
  edoc "Funtoo Linux First Steps" | less

BUGS
====

Please note that the MediaWiki renderer is not perfect and you will likely find pages that it does not render correctly.
Please feel free to open bugs for these issues at https://bugs.funtoo.org. Our renderer is in active development and is
continually improving and becoming more sophisticated.