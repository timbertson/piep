'''
Standard modules:

.. data:: re
.. data:: os
.. data:: sys

Aliases:

.. data:: path

	Alias for the ``os.path`` module

.. data:: Line

	Alias for the ``piep.Line`` class (a subclass of ``str`` containing all the same methods as ``p`` does)

.. data:: List

	Alias for the ``piep.List`` class (a subclass of ``list`` containing all the same methods as ``pp`` does from :class:`piep.BaseList`)

.. data:: devnull

	A readable and writable file pointing to the null device (/dev/null)

Globally-accessible functions:

'''
from __future__ import print_function
import subprocess
import re, os, sys
from .pycompat import *

from piep.sequence import iter_length, BaseList, List, Stream
from piep import line
from piep.shell import Command, check_for_failed_commands
builtins = {}


def add_builtin(fn, name=None):
	name = name or fn.__name__
	if name in builtins:
		print('WARN: overriding piep_builtin %r' % (name,))
	builtins[name] = fn
	return fn

add_builtin(re, 're')
add_builtin(os, 'os')
add_builtin(os.path, 'path')
add_builtin(sys, 'sys')
add_builtin(line.Line, 'Line')
add_builtin(List, 'List')

@add_builtin
def len(obj):
	'''like the builtin ``len``, but works (destructively) on iterators.'''
	try:
		return python_builtin.len(obj)
	except TypeError as e:
		try:
			it = iter(obj)
		except (TypeError, AttributeError) as e2:
			raise e
		return iter_length(it)

@add_builtin
def str(obj):
	'''like the builtin ``str``, but returns an instance of the ``piep.Line`` subclass.'''
	return line.Line(obj)

@add_builtin
def sh(*args, **kwargs):
	'''
	Invoke a shell program and return its output. ``*args`` will be the program name + arguments, and
	``**kwargs`` will be passed through to ``subprocess.Popen``.

	One additional keyword argument is supported - the ``check`` keyword argument (used to suppress an exception when the command fails).

	For more info, see :ref:`running shell commands`
	'''
	return Command(args, **kwargs)

@add_builtin
def spawn(*a, **k):
	'''acts exactly like ``sh``, except that it just returns ``True``.

	For more info, see :ref:`running shell commands`
	'''

	sh(*a, **k)
	return True

devnull = open(os.devnull, 'r+')
add_builtin(devnull, 'devnull')

@add_builtin
@line.wrap_multi
def shellsplit(s):
	'''Split a string much like a shell would.
	(alias for ``shlex.split``)
	'''
	import shlex
	return shlex.split(s)

@add_builtin
def pretty(obj):
	'''
	return a console-cloured pretty printed version of ``obj``
	(like ``repr(obj)``, but coloured)
	'''
	import pygments
	import pygments.lexers
	import pygments.formatters
	return pygments.highlight(repr(obj), lexer=pygments.lexers.get_lexer_by_name('py'), formatter=pygments.formatters.get_formatter_by_name('console')).rstrip('\n\r')

@add_builtin
def _ensure_piep_sequence(pp):
	if not isinstance(pp, BaseList):
		if isinstance(pp, basestring):
			pp = pp.splitlines()
		# if the last expr turned pp into a normal list or some other iterable, fix that...
		cls = Stream
		if isinstance(pp, list):
			cls = List
		try:
			pp = cls(iter(pp))
		except TypeError: # pp was presumably not iterable
			pass
	return pp


@add_builtin
def ignore(*a):
	'''Ignore all arguments and returns ``True``.
	Occasionally useful to evaluate an expression for its
	side-effects without making use of its value.'''
	return True

add_builtin(check_for_failed_commands, "_check_for_failed_commands")
