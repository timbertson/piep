from __future__ import print_function
import subprocess
from piep.error import Exit

active_commands = []
class Command(object):
	def __init__(self, cmd, check=None, **kw):
		self.cmd = cmd

		self.raise_on_error = check
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
		explicitly_suppressed = self.raise_on_error is False
		if self.raise_on_error or (raise_on_error and not explicitly_suppressed):
			if not self.succeeded:
				raise subprocess.CalledProcessError(self.status, ' '.join(self.cmd))
	
	def __nonzero__(self):
		self.wait(raise_on_error = False)
		return self.succeeded

	def __str__(self):
		if not self.checked:
			self.wait()
		return self.stdout.rstrip('\n\r')
	__repr__ = __str__
	str = property(__str__)
	def __add__(self, other):
		return str(self) + other
	def __radd__(self, other):
		return other + str(self)
	
def check_for_failed_commands():
	global active_commands
	for cmd in active_commands:
		if not cmd.checked:
			cmd.wait()
	active_commands = []

