#!/usr/bin/env python

from itertools import *
from pup import shell

class BaseList(object):
	def divide(self, pred, keep_header=True):
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
		"""
		>>> list(Stream(iter([1,2,3,4])).map(lambda x: x % 2 == 0))
		[None, 2, None, 4]
		>>> list(Stream(iter([1,2,3,4])).map(lambda x: x + 1))
		[2, 3, 4, 5]
		"""
		def _transform(line):
			result = fn(line)
			shell.check_for_failed_commands()
			if isinstance(result, bool):
				return line if result else None
			return result
		return self._replace(ifilter(lambda x: x is not None, imap(_transform, self.src)))

	def zip(self, *others):
		return self._replace(izip_longest(self.src, *others))

	def zip_shortest(self, *others):
		return self._replace(izip(self.src, *others))

	def map_index(self, fn):
		i = [0]
		def _call(line):
			try:
				return fn(line, i[0])
			finally:
				i[0] += 1
		return self.map(_call)

	def filter(self, f=None):
		return self._replace(ifilter(f, self.src))

	def join(self, s):
		return type(self)([s.join(list(self))])

	def flatten(self):
		return self._replace(chain.from_iterable(self.src))

	def sort(self):
		return self._replace(sorted(self))

	def reverse(self):
		return self._replace(reversed(self))


class List(list, BaseList):
	def __init__(self, *a, **k):
		super(List, self).__init__(*a,**k)
		self.src = self
	
	def _replace(self, src):
		return List(src)
	
	len = list.__len__

class Stream(BaseList):
	def __init__(self, src):
		self.src = iter(src)
	
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

	def debug(self, note=None):
		return
		a, b = tee(self.src)
		self._replace(b)
		if note is not None:
			print("DEBUG (%s): %r" % (note,list(a)))
		else:
			print("DEBUG: " + repr(list(a)))

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
				self.debug()
			else:
				# normal start to negative end, e.g lst[2:-1]
				self._replace(drop(start, self.src))
				self.debug()
				self._replace(pad_end(abs(stop), self.src))
				self.debug()

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
					self.debug()

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
				self.debug()

		# implement stepping as a post-filter once we've organised the slice
		if step != 1:
			self._replace(islice(self.src, 0, None, step))
		self.debug("end of slice")
		return self
	
	def __reversed__(self):
		rev = reversed(list(self.src))
		self._replace(rev)
		return List(rev)

	def __iter__(self):
		return self.src

	def __nonzero__(self):
		"""
		>>> bool(Stream([1,2,3]))
		True
		>>> bool(Stream([]))
		False
		>>> bool(Stream(repeat(1)))
		True
		"""
		a,b = tee(self.src)
		self._replace(a)
		try:
			next(b)
		except StopIteration:
			return False
		return True

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
			return 'NOPE'
			#raise
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


if __name__ == '__main__':
	import doctest
	doctest.testmod()
