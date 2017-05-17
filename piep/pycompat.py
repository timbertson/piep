import sys
is_python_2 = sys.version_info[0] == 2
if is_python_2:
	import itertools
	from .exec2 import execfn
	map = itertools.imap
	filter = itertools.ifilter
	zip = itertools.izip
	zip_longest = itertools.izip_longest
	import __builtin__ as python_builtin
else:
	from .exec3 import execfn
	basestring = str
	import builtins as python_builtin
