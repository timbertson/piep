import sys
is_python_2 = sys.version_info[0] == 2
def execfn(a,b):
	exec(a,b)

if is_python_2:
	import itertools
	map = itertools.imap
	filter = itertools.ifilter
	zip = itertools.izip
	zip_longest = itertools.izip_longest
	import __builtin__ as python_builtin
else:
	basestring = str
	import builtins as python_builtin
