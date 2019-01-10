from __future__ import print_function
import subprocess
from piep.error import Exit
from piep.line import Line

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
			except OSError as e:
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
	
	def __bool__(self):
		self.wait(raise_on_error = False)
		return self.succeeded
	__nonzero__ = __bool__ # py2 compat

	def __str__(self):
		if not self.checked:
			self.wait()
		return (self.stdout.decode('utf-8') or '').rstrip('\n\r')
	str = property(__str__)
	def __repr__(self): return repr(str(self))
	def __add__(self, other): return str(self).__add__(other)
	def __radd__(self, other): return str(self).__radd__(other)
	def __contains__(self, other): return str(self).__contains__(other)
	def __eq__(self, other): return str(self).__eq__(other)
	def __hash__(self): return str(self).__hash__()
	def __ne__(self, other): return str(self).__ne__(other)
	def __ge__(self, other): return str(self).__ge__(other)
	def __gt__(self, other): return str(self).__gt__(other)
	def __lt__(self, other): return str(self).__lt__(other)
	def __le__(self, other): return str(self).__le__(other)
	def __mod__(self, other): return str(self).__mod__(other)
	def __rmod__(self, other): return str(self).__rmod__(other)
	def __mul__(self, other): return str(self).__mul__(other)
	def __rmul__(self, other): return str(self).__rmul__(other)
	def __getitem__(self, other): return str(self).__getitem__(other)

	def __getattr__(self, attr):
		return getattr(Line(self), attr)
	
def check_for_failed_commands():
	global active_commands
	try:
		for cmd in active_commands:
			if not cmd.checked:
				cmd.wait()
	finally:
		active_commands = []

