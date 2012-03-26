from unittest import TestCase
from test.test_helper import run

class TestJoining(TestCase):
	def test_default_join(self):
		self.assertEqual(
			run('p.split(".")', ['a.b.c']),
			['a b c'])

	def test_custom_join(self):
		self.assertEqual(
			run('--join=/', 'p.split(".")', ['a.b.c']),
			['a/b/c'])

	def test_special_characters_in_join(self):
		self.assertEqual(
			run('--join=\\t', 'p.split(".")', ['a.b.c']),
			['a\tb\tc'])

class TestFilters(TestCase):
	def test_isdigit(self):
		self.assertEqual(
				run('p.isdigit()', ['1', '2', 'three']),
				['1','2'])

	def test_index(self):
		self.assertEqual(
				run('--debug', 'i % 2 == 0', ['0', '1', '2', '3', '4']),
				['0', '2','4'])

class TestLineFunctions(TestCase):
	def test_path_functions(self):
		self.assertEqual(run('p.dirname()', ['a/b/c.py']), ['a/b'])
		self.assertEqual(run('p.ext()', ['a/b/c.py', 'foo']), ['.py', ''])
		self.assertEqual(run('p.extonly()', ['a/b/c.py', 'foo']), ['py'])
		self.assertEqual(run('p.splitext()', ['a/b/c.py']), ['a/b/c .py'])
	
	def test_multiple_path_functions(self):
		self.assertEqual(run('p.upper().ext()', ['a.py']), ['.PY'])
		self.assertEqual(run('p.filename().splitext() | "_".join(p)', ['a/b/c.py']), ['c_.py'])


