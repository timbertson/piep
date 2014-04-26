from unittest import TestCase
from test.test_helper import run

class TestParsing(TestCase):
	def test_complex_parsing(self):
		self.assertEqual(
			run('("%s) %s || %s" % ((i + 1) | 0x00, p, p.upper())) | p', ['a', 'b', 'c']),
			[
				'1) a || A',
				'2) b || B',
				'3) c || C',
				])


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
	
	def test_chaining_of_line_methods(self):
		self.assertEqual(
			run('p.split("-") | p.join(" ")', ['1-2-3']),
			['1 2 3'])

class TestFilters(TestCase):
	def test_isdigit(self):
		self.assertEqual(
				run('p.isdigit()', ['1', '2', 'three']),
				['1','2'])
	
	def test_filter_in_pipeline(self):
		self.assertEqual(
				run('p.isdigit() | "Digit:", p', ['1', '2', 'three']),
				['Digit: 1','Digit: 2'])

	def test_index(self):
		self.assertEqual(
				run('--debug', 'i % 2 == 0', ['0', '1', '2', '3', '4']),
				['0', '2','4'])

class TestLineFunctions(TestCase):
	def test_path_functions(self):
		self.assertEqual(run('p.dirname()'  ,  ['a/b/c.py'])       ,  ['a/b'])
		self.assertEqual(run('p.ext()'      ,  ['a/b/c.py','foo']) ,  ['.py',''])
		self.assertEqual(run('p.extonly()'  ,  ['a/b/c.py','foo']) ,  ['py'])
		self.assertEqual(run('p.splitext()' ,  ['a/b/c.py'])       ,  ['a/b/c .py'])
	
	def test_multiple_path_functions(self):
		self.assertEqual(run('p.upper().ext()'                       ,  ['a.py'])     ,  ['.PY'])
		self.assertEqual(run('p.filename().splitext() | "_".join(p)' ,  ['a/b/c.py']) ,  ['c_.py'])
		self.assertEqual(run('p.splitext().join("-") | repr(p)' ,  ['a/b/c.py'])       ,  ["'a/b/c-.py'"])

	def test_regex_functions(self):
		self.assertEqual(run('p.splitre(" +")'            ,  ['a b   c'])         ,  ['a b c'])
		self.assertEqual(run('p.match("b..")'             ,  ['a beef c'])        ,  ['bee'])
		self.assertEqual(run('p.match("b(..)",1)'         ,  ['a beef c'])        ,  ['ee'])
		self.assertEqual(run('p.match("b(?P<m>..)?","m")' ,  ['a beef c'])        ,  ['ee'])
		self.assertEqual(run('p.match("b(?P<m>..)?","m")' ,  ['a b'])             ,  [])
		self.assertEqual(run('p.matches("b..")'           ,  ['a bee c', 'nope']) ,  ['a bee c'])

	def test_reversed(self):
		self.assertEqual(run('p.reversed()', ['123','abc']), ['321','cba'])

	def test_naked_function(self):
		self.assertEqual(run('repr', ['abc']), [repr('abc')])

	def test_assigning_naked_functions(self):
		self.assertEqual(run('p=repr', ['abc']), [str(repr)])


