from __future__ import print_function
import __builtin__
import subprocess
import re, os, sys

from piep.list import iter_length, BaseList, List, Stream
from piep import line
builtins = {}

def add_builtin(fn, name=None):
	name = name or fn.__name__
	if name in builtins:
		warn('overriding piep_builtin %r' % (name,))
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
	from piep.shell import Command
	return Command(args, **kwargs)

@add_builtin
@line.wrap_multi
def shellsplit(s):
	import shlex
	return shlex.split(s)

add_builtin(re, 're')
add_builtin(os, 'os')
add_builtin(os.path, 'path')
add_builtin(sys, 'sys')
add_builtin(line.Line, 'Line')
add_builtin(List, 'List')

@add_builtin
def _ensure_stream(pp):
	if not isinstance(pp, BaseList):
		# if the last expr turned pp into a normal list or some other iterable, fix that...
		cls = List if isinstance(pp, (list, tuple)) else Stream
		pp = cls(iter(pp))
	return pp
