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

OTHER FEATURES
--------------

**ego boot show defaults**     Show hard-coded (user-overrideable) settings
**ego boot attempt /boot/kernel-foo** ...

DESCRIPTION
-----------

*boot-update* (now *ego boot*) is a system tool developed by Daniel Robbins of Funtoo that will generate a boot loader
*configuration file based on settings stored in etc/boot.conf*. *boot-update* was originally created as an enhanced
*replacement of the upstream GRUB-1.97+ configuration system. GRUB-1.97+'s boot loader configuration file is stored at
**/boot/grub/grub.cfg*, is quite complex and is not intended to be edited directly by system administrators.

*boot-update* has since been extended to support GRUB (*sys-boot/grub*), GRUB Legacy (*sys-boot/grub-legacy*) and LILO
*(*sys-boot/lilo*) to boot systems in MBR (legacy) mode. In addition, GRUB also supports auto-detecting and configuring
*UEFI booting. If boot-update detects that your system has booted in UEFI mode, it will create a UEFI-compatible
*configuration file automatically.

Boot-update allows a single file, */etc/boot.conf*, to store boot-related information in a boot-loader-independent way,
thus simplifying boot loader configuration and providing advanced features to all popular boot loaders.

The normal way to use *boot-update* is to run the command with no options or arguments as root, which will cause a new
boot loader configuration file to be generated. For detailed information on the process that *boot-update* uses to
generate boot loader configuration files, please see *boot.conf(5)*.

.. include:: ../LICENSE

SEE ALSO
--------

boot.conf(5)
