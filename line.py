import os
def delegate(fn, wrap_return=True, multi=False):
	if multi:
		return wrap_multi(fn)
	if wrap_return:
		return wrap(fn)
	return passthru(fn)

def wrap(fn):
	return lambda self, *a, **k: Line(fn(self._Line__str, *a, **k))

def wrap_multi(fn):
	return lambda self, *a, **k: [Line(l) for l in fn(self._Line__str, *a, **k)]

def passthru(fn):
	return lambda self, *a, **k: fn(self._Line__str, *a, **k)


#TODO: get ".".join(Line("a b c").split()) working
class Line(object):
	def __new__(cls, s):
		if s is None:
			return s
		return super(Line, cls).__new__(cls, s)

	def __init__(self, s):
		self.__str = s

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
	splitline = wrap_multi(str.splitlines)
	splittab = wrap_multi(lambda s: s.split('\t'))
	splitcomma = wrap_multi(lambda s: s.split(','))
	splitcolon = wrap_multi(lambda s: s.split(':'))
	splitslash = wrap_multi(lambda s: s.split('/'))
	splitpath = wrap_multi(lambda s: s.split(os.path.sep))

	def __str__(self):
		return self.__str

	# copy all `str` builtins
	capitalize = wrap(str.capitalize)
	center     = wrap(str.center)
	count      = passthru(str.count)
	decode     = wrap(str.decode)
	encode     = wrap(str.encode)
	endswith   = passthru(str.endswith)
	expandtabs = wrap(str.expandtabs)
	find       = passthru(str.find)
	format     = wrap(str.format)
	index      = passthru(str.index)
	isalnum    = passthru(str.isalnum)
	isalpha    = passthru(str.isalpha)
	isdigit    = passthru(str.isdigit)
	islower    = passthru(str.islower)
	isspace    = passthru(str.isspace)
	istitle    = passthru(str.istitle)
	isupper    = passthru(str.isupper)
	join       = wrap(str.join)
	ljust      = delegate(str.ljust)
	lower      = delegate(str.lower)
	lstrip     = delegate(str.lstrip)
	partition  = wrap_multi(str.partition)
	replace    = wrap(str.replace)
	rfind      = passthru(str.rfind)
	rindex     = passthru(str.rindex)
	rjust      = wrap(str.rjust)
	rpartition = wrap_multi(str.rpartition)
	rsplit     = wrap_multi(str.rsplit)
	rstrip     = delegate(str.rstrip)
	split      = wrap_multi(str.split)
	splitlines = wrap_multi(str.splitlines)
	startswith = passthru(str.startswith)
	strip      = wrap(str.strip)
	swapcase   = wrap(str.swapcase)
	title      = wrap(str.title)
	translate  = wrap(str.translate)
	upper      = wrap(str.upper)
	zfill      = wrap(str.zfill)

	# and specials:
	__repr__     = passthru(str.__repr__)
	__getslice__ = wrap(str.__getslice__)
	#__add__      = delegate(str.__add__)
	# coerce EVERYTHING into a string

	@wrap
	def __add__(self, other):
		return self + str(other)

	__contains__ = passthru(str.__contains__)
	__eq__       = passthru(str.__eq__)
	__hash__     = passthru(str.__hash__)
	__format__   = wrap(str.__format__)
	__ge__       = passthru(str.__ge__)
	__getitem__  = wrap(str.__getitem__)
	__getslice__ = wrap(str.__getslice__)
	__gt__       = passthru(str.__gt__)
	__le__       = passthru(str.__le__)
	__len__      = passthru(str.__len__)
	__lt__       = passthru(str.__lt__)
	__lt__       = passthru(str.__lt__)
	__mod__      = wrap(str.__mod__)
	__mul__      = wrap(str.__mul__)
	__ne__       = passthru(str.__ne__)
	__rmod__     = wrap(str.__rmod__)
	__rmul__     = wrap(str.__rmul__)
	__sizeof__   = passthru(str.__sizeof__)

