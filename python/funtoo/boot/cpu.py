from abc import ABCMeta, abstractmethod
from pathlib import Path
from subprocess import getstatusoutput
from typing import Set, Tuple


ScanPaths = Set[str]
StatusAndStr = Tuple[bool, str]


class IAbstractCPU(metaclass=ABCMeta):
	@classmethod
	def __subclasshook__(cls, subclass):
		return (
			hasattr(subclass, "get_absent_microcode_msg")
			and callable(subclass.get_absent_microcode_msg)
			and hasattr(subclass, "get_found_microcode_msg")
			and callable(subclass.get_found_microcode_msg)
		)

	@abstractmethod
	def get_absent_microcode_msg(self) -> str:
		raise NotImplementedError

	@abstractmethod
	def get_found_microcode_msg(self) -> str:
		raise NotImplementedError


class IConcreteCPU(metaclass=ABCMeta):
	@classmethod
	def __subclasshook__(cls, subclass):
		return (
			hasattr(subclass, "has_microcode")
			and callable(subclass.has_microcode)
			and hasattr(subclass, "generate_cpu_microcode_initramfs")
			and callable(subclass.generate_cpu_microcode_initramfs)
		)

	@abstractmethod
	def has_microcode(self) -> bool:
		raise NotImplementedError

	@abstractmethod
	def generate_cpu_microcode_initramfs(self, scanpath: str) -> StatusAndStr:
		raise NotImplementedError


class CPU(IAbstractCPU, metaclass=ABCMeta):
	def __init__(self, scanpaths: ScanPaths):
		self.cpu = self.__class__.__name__
		self._scanpaths = scanpaths

	@property
	@abstractmethod
	def microcode_path(self):
		pass

	@property
	@abstractmethod
	def microcode_packages(self):
		pass

	def _get_deps(self):
		packages = []
		for i in self.microcode_packages:
			p = i["package"]
			u = " ".join(i["required_use_flags"])
			packages.append(p + ("" if len(u) == 0 else f' (with USE="{u}")'))
		return "; ".join(packages)

	def get_absent_microcode_msg(self):
		lvl = "warn"
		deps = self._get_deps()
		return [
			lvl,
			f"{self.cpu} system detected - please emerge {deps} and run "
			+ "boot-update again; boot-update will then patch your system with "
			+ f"the latest {self.cpu} CPU and chipset microcode patches at "
			+ "boot-time, protecting you against important vulnerabilities and errata.",
		]

	def get_found_microcode_msg(self):
		lvl = "note"
		return [lvl, f"{self.cpu} microcode will be loaded at boot-time."]


class Intel(CPU, IConcreteCPU):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._microcode_path = Path("/lib/firmware/intel-ucode")
		self._microcode_packages = [
			{"package": "sys-firmware/intel-microcode", "required_use_flags": []},
			{"package": "sys-apps/iucode_tool", "required_use_flags": []},
		]

	@property
	def microcode_path(self):
		return self._microcode_path

	@property
	def microcode_packages(self):
		return self._microcode_packages

	def has_microcode(self):
		return self.microcode_path.exists()

	def generate_cpu_microcode_initramfs(self, scanpath):
		s, o = getstatusoutput(
			"rm -f %s/early_ucode.cpio; /usr/sbin/iucode_tool --write-earlyfw=%s/early_ucode.cpio /lib/firmware/intel-ucode/* >/dev/null 2>&1"
			% (scanpath, scanpath)
		)
		if s == 0:
			return True, "%s/early_ucode.cpio" % scanpath
		return False, "%s/early_ucode.cpio" % scanpath


class AMD(CPU, IConcreteCPU):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._default_microcode_loc = "/lib/firmware/amd-ucode"
		self._microcode_filename = "amd-uc.img"
		self._microcode_path = self._get_microcode_path()
		self._microcode_packages = [
			{
				"package": "sys-kernel/linux-firmware",
				"required_use_flags": ["initramfs"],
			},
		]

	@property
	def microcode_path(self):
		return self._microcode_path

	@property
	def microcode_packages(self):
		return self._microcode_packages

	def _get_microcode_path(self):
		return Path.joinpath(Path(self._default_microcode_loc), self._microcode_filename)

	def has_microcode(self):
		return self.microcode_path.exists()

	def generate_cpu_microcode_initramfs(self, scanpath):
		s, o = getstatusoutput(
			"cp %s %s >/dev/null 2>&1"
			% (self.microcode_path, scanpath)
		)
		path = Path.joinpath(Path(scanpath), self._microcode_filename)
		return path.exists(), str(path)


# vim: ts=4 sw=4 noet
