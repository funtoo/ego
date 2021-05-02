#!/usr/bin/python3

import subprocess
import threading
import sys
from enum import Enum
from datetime import datetime
from io import StringIO


class Task(object):
	def __init__(self, cmdlist, abortOnError=True):
		self.cmdlist = cmdlist
		self.abortOnError = abortOnError
		self.running = False
		self.complete_on = None
		self.start_on = None
		self.returncode = None
		self._nextTask = None

	def execute(self, runner):
		self.startEvent()
		self.start_on = datetime.now()
		self.running = True
		self.returncode = runner.execute(self.cmdlist)
		self.running = False
		self.complete_on = datetime.now()
		if self.abortOnError is True and self.returncode != 0:
			self.failEvent()
			return False
		else:
			self.completeEvent()
			return True

	@property
	def nextTask(self):
		return self._nextTask

	@nextTask.setter
	def nextTask(self, task):
		self._nextTask = task

	def __iter__(self):
		a = []
		cur = self
		while cur != None:
			a.append(cur)
			cur = cur._nextTask
		return iter(a)

	def startEvent(self):
		pass

	def failEvent(self):
		pass

	def completeEvent(self):
		pass


class TaskList(object):
	def __init__(self):
		self.tasks = []

	def append(self, task):
		self.tasks.append(task)

	def __iter__(self):
		return iter(self.tasks)

	@property
	def returncode(self):
		if len(self.tasks):
			return self.tasks[-1].returncode
		else:
			return None


class OutputMode(Enum):
	NOREDIRECT = 0
	NONE = 1
	OUTFILE = 2


class TaskRunner(object):
	def __init__(self, tasks, stdout=OutputMode.NOREDIRECT, stderr=OutputMode.NOREDIRECT, outfile=None, **kwargs):

		# Supported options:
		# stdout = OutputMode.CONSOLE, stderr = OutputMode.CONSOLE
		# stdout = OutputMode.NONE, stderr = OutputMode.NONE
		# stdout = OutputMode.OUTFILE, stderr = OutputMode.OUTFILE
		# stdout = OutputMode.OUTFILE, stderr = OutputMode.NONE
		# stdout = OutputMode.CAPTURE, stderr = OutputMode.NONE

		if stdout == OutputMode.NONE:
			self.stdout = subprocess.DEVNULL
		elif stdout == OutputMode.NOREDIRECT:
			self.stdout = None
		elif stdout == OutputMode.OUTFILE:
			self.stdout = subprocess.PIPE

		if stderr == None:
			self.stderr = None
		elif stderr == OutputMode.NONE:
			self.stderr = subprocess.DEVNULL
		elif stderr == OutputMode.NOREDIRECT:
			self.stderr = None
		elif stderr == OutputMode.OUTFILE:
			self.stderr = subprocess.PIPE

		self.outfile = outfile
		self.props = kwargs
		self.tasks = tasks

	@property
	def returncode(self):
		return self.tasks.returncode

	def execute(self, cmdlist):
		p1 = subprocess.Popen(cmdlist, shell=False, stdout=self.stdout, stderr=self.stderr)
		if self.outfile:
			for line in p1.stdout:
				self.outfile.write(line.decode(sys.stdout.encoding))
		return p1.wait()

	def startEvent(self):
		pass

	def completeEvent(self):
		pass

	def failEvent(self):
		pass

	def run(self):
		for task in self.tasks:
			if not task.execute(self):
				self.failEvent()
				return False
		self.completeEvent()
		return True


def run(command, quiet=True):
	if isinstance(command, str):
		command = command.split()
	tl = TaskList()
	tl.append(Task(command))
	kwargs = {}
	if quiet:
		kwargs = {"stdout": OutputMode.NONE, "stderr": OutputMode.NONE}
	tr = TaskRunner(tl, **kwargs)
	tr.run()
	return tr.returncode


def run_statusoutput(command):
	if isinstance(command, str):
		command = command.split()
	tl = TaskList()
	tl.append(Task(command))
	outf = StringIO()
	tr = TaskRunner(tl, stdout=OutputMode.OUTFILE, stderr=OutputMode.NONE, outfile=outf)
	tr.run()
	return tr.returncode, outf.getvalue()


class ThreadedTaskRunner(TaskRunner, threading.Thread):
	def __init__(self, tasks, outfile=None, **kwargs):
		TaskRunner.__init__(self, tasks, outfile=outfile, **kwargs)
		threading.Thread.__init__(self)


if __name__ == "__main__":

	# Join tasks together using the .nextTask property.
	# Then use a ThreadedTaskRunner to write output to a file.
	# Commands run in-order in a background thread.

	t1 = Task(["ls", "-l", "/bin"])
	t2 = Task(["ls", "/"])
	t3 = Task(["ls", "/home"])
	t1.nextTask = t2
	t2.nextTask = t3

	with open("/var/tmp/outy2.txt", "w") as myfile:
		tr = ThreadedTaskRunner(t1, outfile=myfile)
		print("START BACKGROUND THREAD")
		tr.start()
		print("CONTROL RETURNED TO PYTHON")
		while True:
			tr.join(0.25)
			if tr.is_alive():
				continue
			else:
				break

	# Join tasks together using a TaskList.
	# Then use a TaskRunner to run and write output to console.
	# Commands run in-order and our current process waits (we gain
	# control when the TaskRunner is complete.)

	t1 = Task(["ls", "-l", "/bin"])
	t2 = Task(["ls", "/"])
	t3 = Task(["ls", "/home"])
	tl = TaskList()
	tl.append(t1)
	tl.append(t2)
	tl.append(t3)

	tr = TaskRunner(tl)
	print("START COMMANDS BUT WAIT FOR THEM TO FINISH")
	tr.run()
	print("CONTROL RETURNED TO PYTHON")

# vim: ts=4 sw=4 noet
