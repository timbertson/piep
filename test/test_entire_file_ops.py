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
	
	def test_chunk_on_predicate(self):
		self.assertEqual(
			run('pp.divide(lambda p: "---" in p) | ".".join(p)',
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
			run('pp.divide(lambda p: "---" in p, keep_header=False) | p.len()',
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


class TestMultipleFileInput(TestCase):
	def test_a_pair_of_files(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write('a\nb\nc\n')
			f.seek(0)

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip(f[0]) | p[0] or "", p[1].upper()', ['1']),
					['1-A','-B','-C'])

	def test_zip_shortest(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write('a\nb\nc\n')
			f.seek(0)

			self.assertEqual(
					run('--join=-',
						'--file=' + f.name, 'pp.zip_shortest(f[0]) | p[0], p[1].upper()', ['1']),
					['1-A'])

