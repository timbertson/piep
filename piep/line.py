import os
def wrap(fn):
	ret = lambda *a, **k: Line(fn(*a, **k))
	ret.__name__ = fn.__name__
	return ret

def wrap_multi(fn):
	ret = lambda *a, **k: [Line(l) for l in fn(*a, **k)]
	ret.__name__ = fn.__name__
	return ret

def passthru(fn):
	return lambda *a, **k: fn(*a, **k)


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
		return os.path.splitext(s)[1]

	@wrap
	def extonly(s):
		ext = os.path.splitext(s)[1]
		return ext[1:] if ext else None

	splitext = wrap_multi(os.path.splitext)
	dirname = wrap(os.path.dirname)
	basename = wrap(os.path.basename)
	filename = basename
	stripext = wrap(lambda s: os.path.splitext(s)[0])
	splitline = wrap_multi(str.splitlines)
	splittab = wrap_multi(lambda s: s.split('\t'))
	splitcomma = wrap_multi(lambda s: s.split(','))
	splitcolon = wrap_multi(lambda s: s.split(':'))
	splitslash = wrap_multi(lambda s: s.split('/'))
	splitpath = wrap_multi(lambda s: s.split(os.path.sep))

	@wrap_multi
	def shellsplit(self):
		import shlex
		return shlex.split(self)

	# copy all `str` builtins
	capitalize = wrap(str.capitalize)
	center     = wrap(str.center)
	encode     = wrap(str.encode)
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

