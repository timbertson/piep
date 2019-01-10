from __future__ import print_function

import sys
import tempfile
from unittest import TestCase
import itertools
from test.test_helper import run, run_full

def write_and_rewind(f, contents):
	f.write(contents.encode('ascii'))
	f.seek(0)

class FileModificationTest(TestCase):
	def test_head(self):
		self.assertEqual(
			run('pp[:2]', ['a','b','c', 'd']),
			['a','b'])

	def test_tail(self):
		self.assertEqual(
			run('pp[-2:]', ['a','b','c', 'd']),
			['c','d'])
	
	def test_str(self):
		self.assertEqual(
			run('str(pp)', ['a','b','c']),
			['a\nb\nc'])
	
	def test_head_works_lazily(self):
		try:
			self.assertEqual(
				run('pp[:4]', itertools.cycle('abc')),
				['a','b','c','a'])
		except MemoryError:
			assert False, "memory exhausted trying to consume infinite sequence"
	
	def test_lists_are_not_downgraded_to_streams(self):
		self.assertEqual(
			run('pp[0], pp[0]', ['1','2']),
			['1','2'])

		self.assertEqual(
			run('list(pp) | pp[0], pp[0]', ['1','2']),
			['1','1'])
	
	def test_strings_are_split_on_lines(self):
		self.assertEqual(
			run('pp[0].split().join("\\n") | p', ['1 2 3']),
			['1','2','3'])

	def test_non_list_objects_are_left_to_their_own_devices_which_may_or_may_not_succeed(self):
		self.assertEqual(
			run('int(pp[0]) | pp + 1', ['1', '2', '3']),
			['2'])

		self.assertRaises((TypeError, AttributeError), lambda: run('int(pp[0]) | p + 1', ['1', '2', '3']))


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
		for var in ('i', 'ff', 'files'):

			with self.assertRaises(AssertionError) as cm:
				print("testing var " + var)
				run(var + ' = 1', [0])
			self.assertEqual(str(cm.exception), "can't assign to `%s` (expression: %s)" % (var,var + ' = 1'))

	def test_explicitly_setting_pp_is_ok(self):
		self.assertEqual(run('pp = [1,2,3] | p', [1]), ['1','2','3'])

	def test_shadowing_a_special_variable_is_ok(self):
		self.assertEqual(run('pp.map(lambda p: 1)', [0]), ['1'])

	def test_file_usage_causes_file_wise_mode(self):
		with tempfile.NamedTemporaryFile() as f:
			write_and_rewind(f, 'a\nb\nc\n')

			self.assertEqual(
				run(
					'--file=' + f.name,
					'len(ff)', [1,2,3,4,5,6]), ['3'])

			with tempfile.NamedTemporaryFile() as f2:
				write_and_rewind(f2, 'a\nb\nc\nd\n')

				self.assertEqual(
					run(
						'--file=' + f.name,
						'--file=' + f2.name,
						'map(len, files)', [1,2,3,4,5,6]), ['3', '4'])

class TestMultipleFileInput(TestCase):
	def test_a_pair_of_files(self):
		with tempfile.NamedTemporaryFile() as f:
			write_and_rewind(f, 'a\nb\nc\n')
			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip(files[0]) | p[0] or "", p[1].upper()', ['1']),
					['1-A','-B','-C'])

	def test_file_alias_when_one_file_used(self):
		with tempfile.NamedTemporaryFile() as f:
			write_and_rewind(f, 'a\nb\nc\n')

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip(ff) | p[0] or "", p[1].upper()', ['1']),
					['1-A','-B','-C'])

	def test_zip_shortest(self):
		with tempfile.NamedTemporaryFile() as f:
			write_and_rewind(f, 'a\nb\nc\n')

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip_shortest(files[0]) | p[0], p[1].upper()', ['1']),
					['1-A'])

class TestOutput(TestCase):
	def test_separating_output_with_null_bytes(self):
		self.assertEqual(
				run_full('--print0', 'p + "_"', 'a\nb\nc'),
				'a_\000b_\000c_')

class TestInput(TestCase):
	def test_self_constructing_pipeline(self):
		self.assertEqual(
				run_full('-n', '[1,2,3] | p + 1', None),
				'2\n3\n4\n')

	def test_explicit_self_constructing_pipeline(self):
		self.assertEqual(
				run_full('--no-input', 'pp = [1,2,3] | p + 1', None),
				'2\n3\n4\n')
