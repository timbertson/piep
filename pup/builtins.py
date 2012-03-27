from __future__ import print_function
import __builtin__
import subprocess

from pup.list import iter_length
from pup import line
builtins = {}

def add_builtin(fn, name=None):
	name = name or fn.__name__
	if name in builtins:
		warn('overriding pup_builtin %r' % (name,))
	builtins[name] = fn
	return fn

@add_builtin
def len(obj):
	try:
		return __builtin__.len(obj)
	except TypeError as e:
		try:
			it = iter(obj)
		except (TypeError, AttributeError) as e2:
			raise e
		return iter_length(it)

@add_builtin
def str(obj):
	return line.Line(obj)

@add_builtin
def sh(*args, **kwargs):
	from pup.shell import Command
	return Command(args, **kwargs)

@add_builtin
@line.wrap_multi
def shellsplit(s):
	import shlex
	return shlex.split(s)

