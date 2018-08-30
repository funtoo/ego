========
ego boot
========

---------------------------------------------
Funtoo Linux Boot Loader Module
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: ##VERSION##
:Manual section: 8
:Manual group: Funtoo Linux Core System

SYNOPSIS
--------

The standard invocation of the command is as follows with no options or arguments, which causes a boot loader
configuration file */etc/boot.conf* to be checked:

  **ego boot**

Typically, **ego boot** would be run if the contents of */etc/boot.conf* were changed by the user, or additional kernels
were installed. This would allow the boot loader menu to reflect these changes. To regenerate configuration for the boot
loader, use the following invocation:

  **ego boot update**

DESCRIPTION
-----------

*boot-update* (now *ego boot*) is a system tool that will generate a boot loader
configuration file based on settings stored in *etc/boot.conf*. *ego boot* was originally created as an enhanced
replacement of the upstream GRUB-1.97+ configuration system. GRUB-1.97+'s boot loader configuration file is stored at
*/boot/grub/grub.cfg*, is quite complex and is not intended to be edited directly by system administrators.

*ego boot* has since been extended to support GRUB (*sys-boot/grub*), GRUB Legacy (*sys-boot/grub-legacy*) and LILO
(*sys-boot/lilo*) to boot systems in MBR (legacy) mode. In addition, GRUB also supports auto-detecting and configuring
UEFI booting. If boot-update detects that your system has booted in UEFI mode, it will create a UEFI-compatible
configuration file automatically.

*ego boot* allows a single file, */etc/boot.conf*, to store boot-related information in a boot-loader-independent way,
thus simplifying boot loader configuration and providing advanced features to all popular boot loaders.

USAGE
-----

Running ``ego boot`` with no options will simply validate the syntax of the */etc/boot.conf* file and exit. If you
would like to update your boot configuration, run ``ego boot update``. This will cause the contents of */etc/boot.conf*
to be parsed and your GRUB (or other boot loader configuration) to be updated, along with installing new CPU microcode
for your CPU if such packages are available (Intel systems only.)

It is also possible to run ``ego boot microcode``, which will update boot microcode without touching your boot loader
configuration.

It is possible to use ``ego boot`` to "attempt" to boot a kernel. By using the following syntax, upon next reboot,
a kernel will be attempted to boot once. If it succeeds, and ``ego boot success`` is run after startup (typically
from ``/etc/local.d``, then the successfully-booted kernel will be "promoted" to be the default kernel. If booting
fails and the system OOPSes or halts, the system will reboot in 10 seconds and continue to use the original default
kernel. If ``ego boot success`` then runs from ``/etc/local.d``, ego will "see" that the attempted kernel is not
running and it will no longer attempt the new kernel on successive boots.

To specify the kernel to attempt, use the following syntax::

    ego boot attempt /boot/kernel-x.y.z

Then ensure that the following command gets run as part of your startup process::

    ego boot success

You can use the invocation ``ego boot attempt default`` to wipe any attempted kernel setting and reset your
boot loader to just boot the default kernel on next boot.

Other invocations supported by ``ego boot`` include ``ego boot --show-defaults``, which will show the default
``/etc/boot.conf`` settings, ``ego boot --check`` performs the same action as ``ego boot`` -- simply validating
the syntax of ``/etc/boot.conf``. ``ego boot --show sect/key`` can be used to display a section/key setting
from ``/etc/boot.conf``. It is also possible to set the default kernel from the command-line by using the
invocation ``ego boot --set-default /boot/kernel-x.y.z``. This will set the specified kernel to be the default
kernel and update your boot configuration accordingly.

.. include:: ../COPYRIGHT.txt

SEE ALSO
--------

boot.conf(5)
