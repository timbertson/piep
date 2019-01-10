from __future__ import print_function
import os
import re

def _apply_doc(ret, fn, doc):
	ret.__name__ = fn.__name__
	if doc is True:
		ret.__doc__ = fn.__doc__
	elif doc is not False:
		ret.__doc__ = doc

def wrap(fn, doc=False):
	ret = lambda *a, **k: Line(fn(*a, **k))
	_apply_doc(ret, fn, doc)
	return ret

def wrap_multi(fn, doc=False):
	def ret(*a, **k):
		from piep.sequence import List
		return List(Line(l) for l in fn(*a, **k))
	_apply_doc(ret, fn, doc)
	return ret

class Line(str):
	def __new__(cls, s, *a, **k):
		if s is None:
			return s
		return super(Line, cls).__new__(cls, s, *a, **k)

	@classmethod
	def add_method(cls, fn, name = None):
		setattr(cls, name or fn.__name__, fn)

	@wrap
	def ext(s):
		'''Return the filename extension (including ".")'''
		return os.path.splitext(s)[1]

	@wrap
	def reversed(s):
		'''Return a reversed version of this string'''
		return s[::-1]

	@wrap
	def extonly(s):
		'''
		Return the filename extension (without the ".")
		If there is no file extension, returns ``None``
		'''
		ext = os.path.splitext(s)[1]
		return ext[1:] if ext else None

	splitext = wrap_multi(os.path.splitext, doc='alias for os.path.splitext(self)')
	dirname = wrap(os.path.dirname, doc='alias for os.path.dirname(self)')
	basename = wrap(os.path.basename, doc='alias for os.path.basename(self)')
	filename = basename
	stripext = wrap(lambda s: os.path.splitext(s)[0], doc='remove filetype extension if present, including "."')
	splitline = wrap_multi(str.splitlines, doc='alias for str.splitlines()')
	splittab = wrap_multi(lambda s: s.split('\t'), doc='split on "\\t"')
	splitcomma = wrap_multi(lambda s: s.split(','), doc='split on ","')
	splitcolon = wrap_multi(lambda s: s.split(':'), doc='split on ":"')
	splitslash = wrap_multi(lambda s: s.split('/'), doc='split on "/"')
	splitpath = wrap_multi(lambda s: s.split(os.path.sep), doc='split on path separator ("/" for unix, "\\" for windows)')

	@wrap_multi
	def shellsplit(self):
		'''shlex.split(self)'''
		import shlex
		return shlex.split(self)

	@wrap_multi
	def splitre(self, regex, *a, **kw):
		'''re.split(regex, self, *a, **kw)'''
		return re.split(regex, self, *a, **kw)

	@wrap
	def match(self, pattern, group=0, flags=0):
		'''extract matched part of the string (or a captured group, if ``group`` is given)'''
		res = re.search(pattern, self, flags=flags)
		return res and res.group(group or 0)

	def matches(self, pattern, group=0, flags=0):
		'''return True or False depending on if the given regex can be found anywhere in the line'''
		return bool(re.search(pattern, self, flags=flags))

	# copy all `str` builtins
	capitalize = wrap(str.capitalize)
	center     = wrap(str.center)
	expandtabs = wrap(str.expandtabs)
	format     = wrap(str.format)
	join       = wrap(str.join)
	ljust      = wrap(str.ljust)
	lower      = wrap(str.lower)
	lstrip     = wrap(str.lstrip)
	partition  = wrap_multi(str.partition)
	replace    = wrap(str.replace)
	rjust      = wrap(str.rjust)
	rpartition = wrap_multi(str.rpartition)
	rsplit     = wrap_multi(str.rsplit)
	rstrip     = wrap(str.rstrip)
	split      = wrap_multi(str.split)
	splitlines = wrap_multi(str.splitlines)
	strip      = wrap(str.strip)
	swapcase   = wrap(str.swapcase)
	title      = wrap(str.title)
	translate  = wrap(str.translate)
	upper      = wrap(str.upper)
	zfill      = wrap(str.zfill)

	# and specials:
	__add__      = wrap(str.__add__)
	__format__   = wrap(str.__format__)
	__getitem__  = wrap(str.__getitem__)
	__mod__      = wrap(str.__mod__)
	__mul__      = wrap(str.__mul__)
	__rmod__     = wrap(str.__rmod__)
	__rmul__     = wrap(str.__rmul__)

