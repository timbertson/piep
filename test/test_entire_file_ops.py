from __future__ import print_function

import sys
import tempfile
from unittest import TestCase
import itertools
from test.test_helper import run

class HeadAndTailTest(TestCase):
	def test_head(self):
		self.assertEqual(
			run('pp[:2]', ['a','b','c', 'd']),
			['a','b'])

	def test_tail(self):
		self.assertEqual(
			run('pp[-2:]', ['a','b','c', 'd']),
			['c','d'])
	
	def test_head_works_lazily(self):
		self.assertEqual(
			run('pp[:4]', itertools.cycle('abc')),
			['a','b','c', 'a'])

class ReplaceWithNonList(TestCase):
	def test_int(self):
		self.assertEqual(
			run('pp.len()', ['1','2','3']), ['3'])

	def test_single_string(self):
		self.assertEqual(
			run('pp.join(".")', ['1','2','3']), ['1.2.3'])

class MultipleOpTest(TestCase):
	def test_multi_head_and_tail(self):
		self.assertEqual(
			run('pp[:5] | "hello", p | pp[-2:]', [1, 2, 3, 4, 5, 6, 7, 8, 9. ,10]),
			['hello 4', 'hello 5'])

class StreamFunctions(TestCase):
	def test_merge(self):
		self.assertEqual(
			run('p.split(".") | pp.merge() | p + "!"', ['1.2.3', '4.5.6']),
			['1!', '2!', '3!', '4!', '5!', '6!'])

	def test_reversed(self):
		self.assertEqual(
			run('pp.reverse()', ['1', '2']),
			['2','1'])

	def test_sort(self):
		self.assertEqual(
			run('pp.sort()', [3,2,1,1]),
			['1', '1','2','3'])

		self.assertEqual(
			run('pp.sort(uniq=True)', [3,2,1,1]),
			['1','2','3'])

	def test_sortby(self):
		self.assertEqual(
				run('p.split() | pp.sortby(lambda x: x[0]) | p[1]', ["0 zero", "3 three", "2 two", "0 zero"]),
			["zero", "zero", "two", "three"])

	def test_sortby_key(self):
		self.assertEqual(
				run('p.split() | pp.sortby(key=0) | p[1]', ["0 zero", "3 three", "2 two"]),
			["zero", "two", "three"])

	def test_sortby_attr(self):
		self.assertEqual(
				run('int(p) | pp.sortby(attr="real")', [3,2,1,1]),
			['1','1','2','3'])

	def test_sortby_method(self):
		self.assertEqual(
				run('pp.sortby(method="lower")', ["bbb", "CCC", "AAA"]),
			["AAA","bbb","CCC"])

	def test_sortby_error_checking(self):
		self.assertRaises(AssertionError, lambda: run('pp.sortby(len, key=0)', []))
		self.assertRaises(AssertionError, lambda: run('pp.sortby(len, attr=0)', []))
		self.assertRaises(AssertionError, lambda: run('pp.sortby(len, method=0)', []))

	def test_uniq(self):
		self.assertEqual(
			sorted(run('pp.uniq()', [5, 4, 3, 2, 1, 2, 3, 4, 5])),
			['1', '2', '3', '4', '5'])

	def test_uniq_stable(self):
		self.assertEqual(
			run('pp.uniq(stable=True)', [5, 4, 1, 5, 2, 1, 3]),
			['5','4','1','2','3'])
	
	def test_chunk_on_predicate(self):
		self.assertEqual(
			run('pp.divide(lambda l: "---" in l) | ".".join(p)',
				[
					'leading',
					'----',
					'chunk 1 line 1',
					'chunk 1 line 2',
					'----',
					'chunk 2 line 1',
					'chunk 2 line 2',
					'---',
					]),
			['leading',
			'----.chunk 1 line 1.chunk 1 line 2',
			'----.chunk 2 line 1.chunk 2 line 2',
			'---']
			)

	def test_chunk_returns_enhanced_list(self):
		self.assertEqual(
			run('pp.divide(lambda l: "---" in l, keep_header=False) | p.len()',
				[
					'leading',
					'----',
					'chunk 1 line 1',
					'chunk 1 line 2',
					'----',
					'chunk 2 line 1',
					'chunk 2 line 2',
					'---',
					]),
			['1', '2', '2'])
	
	def test_reprocess_multi_line_elements(self):
		self.assertEqual(
			run('p + "\\n" + p | pp.flatten()', ['a','b','c']),
			['a','a','b','b','c','c'])

	def test_reprocess_sequence_elements(self):
		self.assertEqual(
			run('[p,p] | pp.merge()', ['a','b','c']),
			['a','a','b','b','c','c'])

class TestFileModeDetection(TestCase):
	def test_assigning_to_any_special_variable_is_disallowed(self):
		for var in ('p', 'pp', 'ff', 'files'):

			with self.assertRaises(AssertionError) as cm:
				print("testing var " + var)
				run(var + ' = 1', [0])
			self.assertEqual(cm.exception.message, "can't assign to `%s` (expression: %s)" % (var,var + ' = 1'))

	def test_shadowing_a_special_variable_is_ok(self):
		self.assertEqual(run('pp.map(lambda p: 1)', [0]), ['1'])

	def test_file_usage_causes_file_wise_mode(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write('a\nb\nc\n')
			f.seek(0)

			self.assertEqual(
				run(
					'--file=' + f.name,
					'len(ff)', [1,2,3,4,5,6]), ['3'])

			with tempfile.NamedTemporaryFile() as f2:
				f2.write('a\nb\nc\nd\n')
				f2.seek(0)

				self.assertEqual(
					run(
						'--file=' + f.name,
						'--file=' + f2.name,
						'map(len, files)', [1,2,3,4,5,6]), ['3', '4'])
	

class TestMultipleFileInput(TestCase):
	def test_a_pair_of_files(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write('a\nb\nc\n')
			f.seek(0)

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip(files[0]) | p[0] or "", p[1].upper()', ['1']),
					['1-A','-B','-C'])

	def test_file_alias_when_one_file_used(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write('a\nb\nc\n')
			f.seek(0)

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip(ff) | p[0] or "", p[1].upper()', ['1']),
					['1-A','-B','-C'])

	def test_zip_shortest(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write('a\nb\nc\n')
			f.seek(0)

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip_shortest(files[0]) | p[0], p[1].upper()', ['1']),
					['1-A'])

