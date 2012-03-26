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

