from itertools import *
from piep import shell
import operator
from piep.line import Line
from .pycompat import *

class BaseList(object):
	'''
	Contains the common methods for :class:`piep.List` and :class:`piep.Stream`
	'''
	def divide(self, pred, keep_header=True):
		'''
		Divide this stream at lines where ``pred`` returns true.
		If ``keep_header`` is set to ``False``, lines matching ``pred`` will not
		be included in the results.

		Each group is returned as a :class:`List` of items.
		'''
		def it(src):
			group = []
			for item in src:
				if pred(item):
					if group:
						yield List(group)
					group = []
					if keep_header:
						group.append(item)
				else:
					group.append(item)
			if group:
				yield List(group)
		return self._replace(it(self.src))

	def map(self, fn):
		def _transform(line):
			result = fn(line)
			if isinstance(result, bool):
				return line if result else None
			return result
		return self._replace(filter(lambda x: x is not None, map(_transform, self.src)))

	def uniq(self, stable=False):
		'''Remove duplicates. Note: if ``stable`` is not given (or is ``False``),
		the order of the return value will be in an arbitrary order.
		If ``stable`` is ``True``, the order will be maintained and only the
		first occurance of a duplicate line will be kept. This is not the default
		because it's much slower. For sorted unique output, try ``sort(uniq=True)``'''
		items = self
		if stable:
			# element order preserved
			seen = {}
			items = [ seen.setdefault(x,x) for x in items if x not in seen ]
		else:
			items = set(items)
		return List(items)

	def zip(self, *others):
		'''Combine this stream with another, yielding sequential pairs from each stream.
		When one sequence is shorter than the other, it's padded with ``None`` elements.
		Basically, ``itertools.zip_longest(self, *others)``
		
		>>> list(Stream([1,2,3,4]).zip(['one','two','three']))
		[(1, 'one'), (2, 'two'), (3, 'three'), (4, None)]
		'''
		return self._replace(zip_longest(self.src, *others))

	def zip_shortest(self, *others):
		'''Like :data:`zip`, but stops once any of the sequences ends.
		
		>>> list(Stream([1,2,3,4]).zip_shortest(['one','two','three']))
		[(1, 'one'), (2, 'two'), (3, 'three')]
		'''
		return self._replace(zip(self.src, *others))

	def map_index(self, fn):
		i = [0]
		def _call(line):
			try:
				return fn(line, i[0])
			finally:
				i[0] += 1
		return self.map(_call)

	def filter(self, f=None):
		'''alias for itertools.ifilter(self, f)'''
		return self._replace(ifilter(f, self.src))

	def join(self, s):
		'''alias for ``s.join(self)``'''
		return s.join(list(self))

	def merge(self):
		'''
		Combine a sequence of iterables into one sequence.
		
		>>> list(Stream([[1],[2,3],[4,5]]).merge())
		[1, 2, 3, 4, 5]
		'''
		return self._replace(chain.from_iterable(self.src))

	def flatten(self):
		r'''
		Combine a sequence of strings (containing newlines) into a sequence of lines.
		
		>>> list(Stream(["a\nb\nc","d\ne"]).flatten())
		['a', 'b', 'c', 'd', 'e']
		'''
		return self._replace(chain.from_iterable(map(lambda x: Line(x).splitlines(), self.src)))

	def sort(self, uniq=False):
		'''
		Return a sorted version of this stream (note: reads entire stream into memory).
		Alias for ``sorted(self)``.

		When ``uniq``=``True``, duplicates are removed from the result.
		'''
		items = set(self) if uniq else self
		return self._replace(sorted(items))

	def sortby(self, fn=None, key=None, attr=None, method=None):
		'''
		Return a sorted version of this stream (note: reads entire stream into memory).
		One (and only one) of the argument types should be provided as the sort key:
		
		- ``fn`` will sort using the return value of calling ``fn`` with each item: ``fn(item)``
		- ``key`` will sort using the given key of each element: ``item[key]``
		- ``attr`` will sort using the given attribute of each element: ``item.attr``
		- ``method`` will sort using the result of calling the given method (with no arguments) on each element: ``item.method()``
		'''
		defined_items = list(filter(lambda x: x is not None, (fn, key, attr, method)))
		assert len(defined_items) == 1, "exactly one of (fn, key, attr, method) arguments allowed to `sortby` method (you gave %s: %r)" % (len(defined_items), defined_items)

		if key is not None: fn = operator.itemgetter(key)
		if attr is not None: fn = operator.attrgetter(attr)
		if method is not None: fn = operator.methodcaller(method)
		return self._replace(sorted(self, key=fn))

	def reverse(self):
		'''
		Return a reversed version of this stream (note: reads entire stream into memory)
		Alias for ``reversed(self)``
		'''
		return self._replace(reversed(self))


class List(list, BaseList):
	def __init__(self, *a, **k):
		super(List, self).__init__(*a,**k)
		self.src = self
	
	def _replace(self, src):
		return List(src)
	
	len = list.__len__

class _SafeBoolIterator(object):
	@classmethod
	def of_iter(cls, it):
		try:
			head = next(it)
		except StopIteration:
			return _EmptyIterator()
		else:
			return _NonEmptyIterator(head, it)

	def __iter__(self): return self

	# py2 compat
	def next(self): return self.__next__()
	def __nonzero__(self): return self.__bool__()

class _EmptyIterator(_SafeBoolIterator):
	def __next__(self): raise StopIteration
	def __bool__(self): return False

class _NonEmptyIterator(_SafeBoolIterator):
	"""
	An iterator which keeps a reference to its own `head`,
	useful to check the first element without actually
	consuming it.

	>>> it = _NonEmptyIterator(1, [2,3])
	>>> list(it)
	[1, 2, 3]
	"""
	def __init__(self, head, tail):
		self._replace(head, iter(tail))

	def _replace(self, head, tail):
		self._head = head
		self._tail = tail
		self._it = None

	def __bool__(self):
		if self._it is None:
			# head not consumed
			return True
		else:
			# head consumed, consume the next item (if any) and
			# keep it as the new head
			try:
				head = next(self._it)
			except StopIteration:
				return False
			else:
				self._replace(head, self._tail)

	def __iter__(self):
		return self

	def __next__(self):
		if self._it is None:
			self._it = self._tail
			return self._head
		else:
			return next(self._it)

class Stream(BaseList):
	def __init__(self, src):
		self._replace(src)
	
	def __getitem__(self, n):
		"""
		>>> Stream([1,2,3,4,5,6,7])[2]
		3
		>>> Stream([1,2,3,4,5,6,7])[-2]
		6
		>>> list(Stream([1,2,3,4,5,6,7])[3:5])
		[4, 5]
		>>> list(Stream([1,2,3,4,5,6,7])[3:-2])
		[4, 5]
		>>> list(Stream([1,2,3,4,5,6,7])[:-2])
		[1, 2, 3, 4, 5]
		>>> list(Stream([1,2,3,4,5,6,7])[-2:])
		[6, 7]
		>>> list(Stream([1,2,3,4,5,6,7])[-4:-5])
		[]
		>>> list(Stream([1,2,3,4,5,6,7])[-4:-2])
		[4, 5]
		>>> list(Stream([1,2])[-4:])
		[1, 2]
		>>> list(Stream([1])[:2])
		[1]
		"""
		if isinstance(n, slice):
			return self._slice(n.start, n.stop, n.step)
		try:
			if n < 0:
				return pad_end(abs(n), self.src).end[0]
			elif n > 0:
				drop(n, self.src)
			return next(self.src)
		except StopIteration:
			raise IndexError(n)

	def _replace(self, src):
		self.src = iter(src)
		return self
	
	# unfortunately, list(item) will call __len__
	# and therefore drain the iter if it's defined
	# (so we just have a `.length` method instead)
	def len(self):
		return iter_length(self.src)

	def __add__(self, other):
		return list(self) + other

	def __radd__(self, other):
		return other + list(self)

	def _slice(self, start, stop, step):
		start = start or 0
		step = step or 1

		negative_stop = stop is not None and stop < 0
		positive_stop = stop is not None and stop >= 0

		# START
		if start >= 0:
			if positive_stop or stop is None:
				# normal slice
				self._replace(islice(self.src, start, stop))
			else:
				# normal start to negative end, e.g lst[2:-1]
				self._replace(drop(start, self.src))
				self._replace(pad_end(abs(stop), self.src))

		else: # start < 0
			if negative_stop:
				# e.g lst[-5:-2]
				# get the padded end
				padded = pad_end(abs(stop), self.src)
				if start >= stop:
					self._replace([])
				else:
					start -= stop
					self._replace(pad_end(abs(start), padded).end)

			elif stop is None:
				self._replace(pad_end(abs(start), self.src).end)

			else: # stop is positive, e.g lst[-3,2]
				try:
					first_half = take(stop, self.src)
					num_remaining = iter_length(self.src)
					if num_remaining > abs(start):
						raise StopIteration() # not really, but the slice will be empty
				except StopIteration:
					self._replace([])
				else:
					start += num_remaining # we already "chopped" num_remaining off the end of the original sequence
					self._replace(first_half[start:])

		# implement stepping as a post-filter once we've organised the slice
		if step != 1:
			self._replace(islice(self.src, 0, None, step))
		return self
	
	def __reversed__(self):
		rev = reversed(list(self.src))
		self._replace(rev)
		return List(rev)

	def __iter__(self):
		return self.src

	def __str__(self):
		return Line("\n".join(list(self.src)))

	def __repr__(self):
		return repr(list(self.src))

	def __bool__(self):
		"""
		>>> bool(Stream([1,2,3]))
		True

		>>> bool(Stream([]))
		False

		>>> bool(Stream(repeat(1)))
		True

		# ensure `bool` doesn't consume `head`
		>>> s = Stream(iter([1]))
		>>> bool(s)
		True
		>>> bool(s)
		True
		>>> bool(s)
		True
		"""
		# force self.src to be a bool-safe iterator first
		if not isinstance(self.src, _SafeBoolIterator):
			self._replace(_SafeBoolIterator.of_iter(self.src))
		return bool(self.src)

	__nonzero__ = __bool__

class pad_end(object):
	"""
	Creates an iterator with a "padded end". e.g
	an iterator with 2 padding at the end will maintain
	a buffer of 2 items, and stop 2 items before
	the end of the underlying iterator.

	You can call `.end` to get the last `n` items as a list.
	NOTE: this will exhaust the underlying iterator
	first.

	>>> list(pad_end(2, iter([1,2,3,4])))
	[1, 2]
	>>> pad_end(2, iter([1,2,3,4])).end
	[3, 4]
	>>> pad_end(4, iter([1,2,3,4,5,6,7,8,9])).end
	[6, 7, 8, 9]
	"""
	def __init__(self, n, it):
		self._n = n
		self._it = it
		self._fill_cache()
	
	def __iter__(self):
		return self

	def _fill_cache(self):
		"""fills cache with up to `self._n` items"""
		self._cache = []
		self._cache_head = 0

		assert self._n > 0
		n = 0
		try:
			while n < self._n:
				self._cache.append(next(self._it))
				n += 1
		except StopIteration: pass

	def _rotate(self, item):
		"""add the given item to the end of the cache, pushing off (and returning) the current head"""
		try:
			old_item = self._cache[self._cache_head]
		except IndexError as e:
			print("Key Error %s" % (e,))
			print("cache = %r" % (self._cache))
			print("cache head = %r" % (self._cache_head))
			raise
		self._cache[self._cache_head] = item
		self._cache_head = (self._cache_head + 1) % self._n
		return old_item
	@property
	def end(self):
		exhaust(self)
		return self._cache[self._cache_head:] + self._cache[:self._cache_head]

	def __next__(self):
		return self._rotate(next(self._it))
	next = __next__ # for python2


def exhaust(iter):
	try:
		while True:
			next(iter)
	except StopIteration:
		pass

def iter_length(iter):
	"""
	>>> iter_length(iter([1,2,3]))
	3
	>>> iter_length(iter([]))
	0
	"""
	n = 0
	try:
		while True:
			next(iter)
			n+=1
	except StopIteration:
		return n

def drop(n, it, stop_short=False):
	"""
	>>> list(drop(3, iter([1,2,3,4,5])))
	[4, 5]
	>>> list(drop(10, iter([1,2,3,4,5]), True))
	[]
	"""
	try:
		while n>0:
			next(it)
			n-=1
		return it
	except StopIteration:
		if stop_short:
			return iter([])
		raise

def take(n, it, stop_short=False):
	"""
	>>> list(take(3, iter([1,2,3,4,5])))
	[1, 2, 3]
	>>> list(take(0, iter([1,2,3,4,5])))
	[]
	>>> list(take(3, iter([1]), True))
	[1]
	"""
	results = []
	try:
		while n>0:
			results.append(next(it))
			n-=1
		return results
	except StopIteration:
		if stop_short:
			return results
		raise
