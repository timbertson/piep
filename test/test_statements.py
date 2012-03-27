from unittest import TestCase
from test.test_helper import run

class TestEval(TestCase):
	def test_import_assignment(self):
		self.assertEqual(
				run('--eval=from cgi import escape as quote', 'quote(p)', ['a&b']),
				['a&amp;b'])

	def test_import_shorthand(self):
		self.assertEqual(
				run('--import=cgi', 'cgi.escape(p)', ['a&b']),
				['a&amp;b'])

	def test_globals(self):
		self.assertEqual(
				run('--eval=PREFIX="----"', '[PREFIX] + pp', ['line']),
				['----', 'line'])

class TestHistory(TestCase):
	def test_restoring_previous_results(self):
		self.skipTest("pending")
		self.assertEqual(
				run('p0 = p | p.extonly() | p, "is a", p0', ['a.py','b.jpg']),
				['a.py is a py', 'b.jpg is a jpg'])
