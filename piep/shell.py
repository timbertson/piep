from __future__ import print_function
import subprocess
from piep.error import Exit

active_commands = []
class Command(object):
	def __init__(self, cmd, **kw):
		self.cmd = cmd

		self.raise_on_error = kw.pop('check', True)
		defaults = dict(stdout = subprocess.PIPE)
		defaults.update(kw)
		self.kwargs = defaults

		active_commands.append(self)
		self.checked = False
		self.proc = None
		self.stdout = None
		self.stderr = None
	
	def _spawn(self):
		if self.proc is None:
			try:
				self.proc = subprocess.Popen(self.cmd, **self.kwargs)
			except OSError, e:
				raise Exit("error executing %r: %s" % (list(self.cmd), e))
	
	def wait(self, raise_on_error=True):
		self._spawn()
		self.checked = True
		(self.stdout, self.stderr) = self.proc.communicate()
		self.ended = True
		self.status = self.proc.returncode
		self.succeeded = self.status == 0
		if raise_on_error and self.raise_on_error and not self.succeeded != 0:
			raise subprocess.CalledProcessError(self.status, repr(list(self.cmd)))
	
	def __nonzero__(self):
		self.wait(raise_on_error = False)
		return self.succeeded

	def __str__(self):
		if not self.checked:
			self.wait()
		return self.stdout.rstrip('\n\r')
	__repr__ = __str__
	
def check_for_failed_commands():
	global active_commands
	for cmd in active_commands:
		if not cmd.checked:
			cmd.wait()
	active_commands = []

