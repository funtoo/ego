=========
boot.conf
=========

---------------------------------------------
Funtoo global boot loader configuration file
---------------------------------------------

:Author: Daniel Robbins <drobbins@funtoo.org>
:Version: ##VERSION##
:Manual section: 5
:Manual group: Funtoo Linux Core System

SYNOPSIS
--------

  */etc/boot.conf*

DESCRIPTION
-----------

The data in */etc/boot.conf* is used by *ego-boot(8)* to generate specific
configuration files for various boot loaders as necessary.

The benefit of */etc/boot.conf* is that it provides a single location to
store all boot-related information. It also provides a single, consistent file
format and feature set for configuring all boot loaders.

For MBR booting, GRUB, GRUB (legacy) and LILO boot loaders are supported. For
UEFI booting, GRUB is supported. When using GRUB, boot-update will auto-enable
UEFI boot configuration if it sees that your system has been booted in UEFI mode.
Otherwise, MBR (legacy) boot mode will be used.

*boot-update(8)* utilizes */etc/boot.conf* to provide a consistent process for
updating boot loader configuration, regardless of the actual boot loader used.

Here is a sample */etc/boot.conf* configuration file:

.. include:: ../etc/boot.conf.example
   :literal:

Sections
~~~~~~~~

Sections are specified by an alphanumeric name, followed by a space and a *{*.
A section ends when a single *}* appears on a line.

There are special *built-in* sections that are expected to be found by the
framework and used for configuation settings. You can not use the name of
a *built-in* section as the name of a boot entry.
Currently these are all *built-in* sections:
*boot*, *color*, *default*, *grub*, *grub-legacy*, *lilo*, *serial*

In addition, other sections can be created. Any sections with non-builtin names
are recognized as boot entry definitions. For example, the sections *"Funtoo
Linux"* and *"Funtoo Linux genkernel"* define boot entries. Due to
*/etc/boot.conf*'s wildcard support, a single boot entry section in the
configuration file may generate multiple actual boot entries for the boot
loader, depending on how many matches are found. Wildcard support will be
explained later in this document.

Default Section
~~~~~~~~~~~~~~~

In addition, there is a special section named *default* which is used to
specify default settings for the boot entry sections. *boot-update* has several
reasonable default built-in settings that can be overridden. For example, if
you leave out the *boot/timeout* setting, the boot menu timeout will default to
5 seconds. To see all built-in settings, type *boot-update --showdefaults*.

Linux Boot Entries
~~~~~~~~~~~~~~~~~~

There are four critical parameters that are used in boot entry and *default*
sections -- *type*, *kernel*, *initrd* and *params*. *type* defaults
to "linux" and informs *boot-update* that we are specifying a Linux boot
entry.  It can be set to other values to tell *boot-update* that we are
specifying a Microsoft Windows 7 boot entry, for example.

Linux Kernel Wildcards
~~~~~~~~~~~~~~~~~~~~~~

The *kernel* variable specifies one or more kernels, using exact kernel file
names or wildcards. Again, note that it is possible for one boot entry in
*/etc/boot.conf* to generate *multiple* boot entries for your boot loader if
wildcards are used or multiple kernels are listed -- one boot entry will be
generated for each matching kernel found.

So, for example, the following
*/etc/boot.conf* could generate two boot entries named "Funtoo Linux -
bzImage" and "Funtoo Linux - bzImage-new"::

        "Funtoo Linux" {
                kernel bzImage bzImage-new
        }

The *[-v]* wildcard, which can only appear once per filename, can be used at
the end of a kernel image name to match the base name, or any combination of
the base name, plus a hypen and any additional text::

        "Funtoo Linux" {
                kernel bzImage[-v]
        }

Above, *bzImage[-v]* will match *bzImage* as well as *bzImage-**.

In addition, *boot.conf* now supports the inclusion of arbitrary glob wildcards
within brackets, which work similarly to *[-v]*, above::

        "Funtoo Linux" {
                kernel bzImage[-2.6*]
        }

The above wildcard will match "bzImage", "bzImage-2.6.18", and "bzImage-2.6.24".

Remember that wildcards are optional. If you don't want to deal with them, you
can just provide the name of a kernel image.

initrd/initramfs
~~~~~~~~~~~~~~~~

The *initrd* variable specifies one or more initrds or initramfs images, like
this::

        "Funtoo Linux" {
                kernel bzImage
                initrd initramfs.igz
        }

*initrd* also allows the use of the *[-v]* wildcard to allow you to create
matching pairs of kernels and initrds on disk that boot-update will associate
with one another automatically by suffix. Here's how it works -- assume you have
the following boot entry::

        "Funtoo Linux" {
                kernel bzImage[-v]
                initrd initramfs[-v]
        }

The */etc/boot.conf* entry above will look for all kernels matching *bzImage*
and *bzImage-** and generate a boot entry for each one. For the boot entry for
*bzImage*, the *initramfs[-v]* wildcard will pull in the initramfs *initramfs*
if it exists -- if not, it will be skipped. For the boot entry for
*bzImage-2.6.24*, the initramfs *initramfs-2.6.24* will be used if it exists.

If you are using the enhanced glob wildcard functionality in your *kernel*
option (such as *bzImage[-2.6*]*, above), then remember that you should still
use *[-v]* in your *initrd* option. *[-v]* is the only pattern that is supported
for initrds.

Multiple initrds
~~~~~~~~~~~~~~~~

Since Linux allows multiple initramfs images to be loaded at boot time, you can
specify more than one initrd in a boot entry, and the specified initrds will be
loaded in succession abt boot time. Note that this is different from the
*kernel* option - where multiple matches will generate multiple boot entries,
since you can only load one kernel at boot. Here's an example::

        "Funtoo Linux" {
                kernel bzImage
                initrd initramfs-1.igz initramfs-2.igz
        }

In the above example, a single boot entry will be generated, which will load
*initramfs-1.igz* and *initramfs-2.igz* as the primary and secondary initramfs
respectively, and then boot the kernel *bzImage*.

Note that the *+=* operator can be used to either extend the default initramfs
setting or to specify multiple initramfs images over multiple lines. Here's
a boot entry that is equivalent to the previous example::

        "Funtoo Linux" {
                kernel bzImage
                # load initramfs-1.igz:
                initrd initramfs-1.igz
                # also load initramfs-2.igz:
                initrd += initramfs-2.igz
        }

And in the following example, the initial *+=* tells coreboot to append
*initramfs-1.igz* to the default initramfs list::

        "Funtoo Linux" {
                kernel bzImage
                # load our default initramfs image(s), plus this one:
                initrd += initramfs-1.igz
        }

Parameters
~~~~~~~~~~

The *params* variable specifies kernel parameters used to boot the kernel.
Typical kernel parameters, such as *init=/bin/bash*, *root=/dev/sda3* or others
can be specified as necessary. Here's a sophisticated example from Andreas
Matuschek that was posted on the funtoo-dev mailing list::

        "Funtoo Linux On Ice" {
                params root=/dev/sda2
                params += rootfstype=jfs
                params += usbcore.autosuspend=1
                params += acpi_sleep=s3_bios,s3_mode
                params += hpet=force
                params += video=radeonfb:ywrap,mtrr:1,1024x768-32@60
                params += quiet
                params += splash=silent,kdgraphics,theme:natural_gentoo
                params += CONSOLE=/dev/tty1
                kernel vmlinuz[-v]
                initrd ramfs
        }

As you can see, when  *+=* is used as the first argument for *params*, the
default setting can be *extended* with additional parameters. If the first
*params root=/dev/sda2* line was instead written as *params += root=/dev/sda2*,
then all the parameters specified in this boot entry would *extend* the default
params settings. But in this case, Andreas specified the first *params*
parameter in this boot entry without a *+=*, so his settings replace the
default settings.

Note that when serial console support is enabled, the appropriate parameters
for serial support (from the serial section) will be added to params.

Special Parameters
~~~~~~~~~~~~~~~~~~

**+=**
  When *+=* is specified at the beginning of the first *params*, *initrd* or
  *kernel* definition in a section, then the arguments after the *+=* will be
  added to the default settings defined in *default* (type *boot-update
  --showdefaults* to see default settings.)  In addition, multiple *params*,
  *initrd* or *kernel* lines can appear in a section, as long as the successive
  lines begin with *+=*. This allows these values to be defined over multiple
  lines.

**root=auto**
  When *root=auto* is evaluated, the framework will look at */etc/fstab* to
  determine the root filesystem device. Then *root=auto* will changed to
  reflect this, so the actual parameter passed to the kernel will be something
  like *root=/dev/sda3* .

**rootfstype=auto**
  In a similar fashion to *root=auto*, *rootfstype=auto* will be
  replaced with something like *rootfstype=ext4*, with the filesystem type
  determined by the setting in */etc/fstab*.

**real_root=auto**
  This special parameter is useful when using *genkernel* initrds that expect a
  *real_root* parameter. When specified, any *root=* options already specified
  (including *root=auto*) will be removed from *params*, and *real_root* will
  be set to the root filesystem based on */etc/fstab*, so you'll end up with a
  setting such as *real_root=/dev/sda3*.

Linux distributions on separate partitions
------------------------------------------

*boot-update* supports creating boot entries for Linux distributions installed
on separate partitions. In order for *boot-update* to find the kernels and initrds
located on other partitions you have to create a mount point for the partition.
After creating a mount point you must specify the absolute path to the kernels
using the scan variable::

	"Debian Sid" {
		scan /mnt/debian/boot
		kernel vmlinuz[-v]
		initrd initrd.img
		params root=/dev/sdb1
	}

Note that you must also set *params root=/dev/<root>* to the correct root
partition in order to override the default *root=auto* setting. At this time
*boot-update* does not support auto detecting for other Linux systems.

If you would like boot-update to auto mount the partition whenever it is ran, you
must create an entry for mounting it in */etc/fstab*. Otherwise you will need to
mount the partition before running *boot-update*.

Alternate OS Loading
--------------------

Boot entries can be created for alternate operating systems using the following
approach::

        "Windows 7" {
                type win7
                params root=/dev/sda6
        }


The *type* variable should be set to one of the operating system names that
*boot-update* recognizes (case-insensitive,) which are:

- linux (default)
- dos
- msdos
- Windows 2000
- win2000
- Windows XP
- winxp
- Windows Vista
- vista
- Windows 7
- win7
- Windows 8
- win8
- Windows 10
- win10
- Haiku
- Haiku OS

For non-Linux operating systems, the *params* variable is used to specify the
root partition for chain loading. For consistency with Linux boot entries, the
syntax used is *root=device*.

Users can manually set the chainloader option if they require a special value 
other than the normal default set by boot.conf::
        "Windows 10" {
                type win10
                params root=/dev/sda6
		params += chainloader=+4
        }


*boot* Section
----------------

*boot :: generate*
~~~~~~~~~~~~~~~~~~~~

Specifies the boot loader that *boot-update* should generate a configuration
files for. This setting should be a single string, set to one of *grub*,
*grub-legacy* or *lilo*. Defaults to *grub*.


*boot :: timeout*
~~~~~~~~~~~~~~~~~~~

Specifies the boot loader timeout, in seconds. Defaults to *5*.

*boot :: default*
~~~~~~~~~~~~~~~~~~~

Use this setting to specify the boot entry to boot by default. There are two
ways to use this setting.

The first way is to specify the filename of the kernel to boot by default. This
setting should contain no path information, just the kernel image name.  This
is the default mechanism, due to the setting of *bzImage*.

Alternatively, you can also specify the literal name of the boot entry you want
to boot. This is handy if you want to boot a non-Linux operating system by
default. If you had the following boot entry::

        "My Windows 7" {
                type win7
                params root=/dev/sda6
        }

...then, you could boot this entry by default with the following boot section::

        boot {
                generate grub
                default My Windows 7
        }

This is also a handy mechanism if you want to boot the most recently created
kernel by default. The kernel with the most recent modification time will be
selected. To do this, specify the name of the boot entry rather than
the kernel image name::

        boot {
                default "Funtoo Linux"
        }

If multiple "Funtoo Linux" boot entries are created, the one that has the most
recently created kernel (by file modification time) will be booted by default.

Also note that if no ``default`` setting is specified, or no match is found,
boot-update will select the most recent kernel by file modification time and
set it as the default selection for booting.

Note that double-quotes are optional both in section names and in the
*boot/default* value.

*boot :: bootdev*
~~~~~~~~~~~~~~~~~~~

Specifies which device or partition to install the bootloader to. This is
currently only used for lilo and is the equivalent of setting "boot = <bootdev>"
in ``/etc/lilo.conf``. Other bootloaders will just ignore it if set::

        boot {
                bootdev /dev/sda
        }


*boot :: terminal*
~~~~~~~~~~~~~~~~~~

Specifies the terminal mode: either "serial" or "video". Defaults to "video".
This setting affects your boot-loader input/output as well as your kernel's
output.

If you set it to "serial", use the "serial" section (see below) to set serial
options.

*serial* Section
----------------

Specifies the serial port settings for both boot-loader and kernel. Possible
values are:

*unit* (tty number, defaults to 0)
*speed* (bps, defaults to 115200)
*word* (word size, defaults to 8)
*parity* (yes/no, defaults to no)
*stop* (stop bit, defaults to 1)

*default* and Boot Entry Sections
---------------------------------

*default :: type*
~~~~~~~~~~~~~~~~~~~

Specifies the boot entry type; defaults to *linux*. Currently, DOS/Windows boot
entries are also supported. Set to one of: *linux*, *dos*, *msdos*, *Windows
2000*, *win2000*, *Windows XP*, *winxp*, *Windows Vista*, *vista*, *Windows 7*,
*win7*, *win8*, *win10*. Here's how to specify a Windows 7 boot entry, which will automatically
use the proper chainloader +4 parameter to load Microsoft Windows 7::

        "My Windows 7" {
                type win7
                params root=/dev/sda6
        }

*default :: scan*
~~~~~~~~~~~~~~~~~~~

This setting specifies one or more directories to scan for kernels and
initrds. Defaults to ``/boot``.

*default :: kernel*
~~~~~~~~~~~~~~~~~~~~~

This setting specifies kernel image name, names or patterns, to find kernels to
generate boot menu entries for. The path specified in the *scan* setting is
searched. Glob patterns are supported, but only one glob pattern may appear per
filename. The special pattern `[-v]` is used to match a kernel base name (such
as *bzImage*) plus all kernels with an optional version suffix beginning with a
*-*, such as *bzImage-2.6.24*. In addition, arbitrary globs can be specified,
such as *bzImage[-2.6.\*]* If more than one kernel image matches a pattern, or
more than one kernel image is specified, then more than one boot entry will be
created using the settings in this section.

*default :: initrd*
~~~~~~~~~~~~~~~~~~~~~

This setting specifies initrd/initramfs image(s) to load with the menu entry.
If multiple initrds or initramfs images are specified, then *all* specified
images will be loaded for the boot entry. Linux supports multiple initramfs
images being specified at boot time. Glob patterns are supported. The special
pattern *[-v]* is used to find initrd/initramfs images that match the
*[-v]* pattern of the current kernel.  For example, if the current menu
entry's kernel image has a *[-v]* pattern of *-2.6.24*, then
*initramfs[-v]* will match *initramfs-2.6.24*. If the current menu entry
had a *[-v]* pattern, but it was blank (in the case of *bzImage[-v]*
finding a kernel named *bzImage*,) then *initramfs[-v]* will match
*initramfs*, if it exists.

*default :: params*
~~~~~~~~~~~~~~~~~~~~~

This setting specifies the parameters passed to the kernel. This option
appearing in the *default* section can be extended in specific menu sections
by using the *+=* operator. The special parameters *root=auto*,
*rootfstype=auto* and *real_root=auto* are supported, which will be
replaced with similar settings with the *auto* string replaced with the
respective setting from */etc/fstab*. Defaults to *root=auto
rootfstype=auto*.

*display* Section
-------------------

*display :: gfxmode*
~~~~~~~~~~~~~~~~~~~~~~

Specifies the video mode to be used by the boot loader's menus. This value is
also inherited and used as the video mode for the kernel when a graphical boot
(*uvesafb*, *vesafb-tng*) is used. This option is only supported for
*grub*. Default value is "text" for MBR booting, or "640x480" for UEFI booting.

*display :: background*
~~~~~~~~~~~~~~~~~~~~~~~~

Specifies the graphical image to display at boot. The specified file should
exist within ``/boot``, and the path to the file should be specified relative
to ``/boot``. A file with a "jpg", "jpeg", "png", or "tga" extension
(capitalized or lowercase) will be recognized and used. This option is only
supported for *grub*, and defaults to being unset.

*display :: font*
~~~~~~~~~~~~~~~~~

Specifies a font used to display text in graphical mode (ie. when ``display::gfxmode`` is enabled) at boot. Defaults to
``unifont.pf2``, which is included with Funtoo's `grub` ebuild, or ``unicode.pf2``, which is included in Gentoo's
ebuild. If the font does not exist in ``/boot/grub`` or ``/boot/grub/fonts``, it will be copied from ``/usr/share/grub``
or ``/usr/share/grub/fonts``, if it exists. This option is only supported for *grub*, and will only be enabled when a
``gfxmode`` has been specified.

*color* Section
-----------------

Currently, the color options are only supported for *grub*.

*color :: normal*
~~~~~~~~~~~~~~~~~~~

Specifies the regular display colors in *fg/bg* format. Defaults to *cyan/blue*.
**HINT**: a *black* background will be transparent when a background image is
specified.

*color :: highlight*
~~~~~~~~~~~~~~~~~~~~~~

Specifies the menu highlight colors in *fg/bg* format. Defaults to *blue/cyan*.
**HINT**: a *black* background will be transparent when a background image is
specified.

.. include:: ../LICENSE

SEE ALSO
--------

boot-update(8), genkernel(8)
