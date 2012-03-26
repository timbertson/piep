from __future__ import print_function

import sys
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
		self.skipTest('broken')
		self.assertEqual(
			run('pp.join(".")', ['1','2','3']), ['1.2.3'])

class MultipleOpTest(TestCase):
	def test_multi_head_and_tail(self):
		self.assertEqual(
			run('pp[:5] | "hello", p | pp[-2:]', [1, 2, 3, 4, 5, 6, 7, 8, 9. ,10]),
			['hello 4', 'hello 5'])

class LazyListFunctions(TestCase):
	def test_flatten(self):
		self.assertEqual(
			run('p.split(".") | pp.flatten() | p + "!"', ['1.2.3', '4.5.6']),
			['1!', '2!', '3!', '4!', '5!', '6!'])
	def test_reversed(self):
		self.assertEqual(
			run('pp.reverse()', ['1', '2']),
			['2','1'])

