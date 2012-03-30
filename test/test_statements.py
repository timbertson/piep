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
		self.assertEqual(
				run('p0 = p | p.extonly() | p0, "is a", p', ['a.py','b.jpg']),
				['a.py is a py', 'b.jpg is a jpg'])
	
	def test_aliases_dont_affect_future_p_values(self):
		self.assertEqual(
			run('--join=.', 'ext = p.extonly() | p.upper() | p.stripext() | p, ext', ['a.py','b.py']),
			['A.py', 'B.py'])
	
	def test_cant_modify_pp_and_maintain_history(self):
		self.assertRaises(NameError, lambda: run('p0=p | pp | p0,p', ['a']))
	
	def test_assigning_from_pp(self):
		self.assertEqual(
			run('header = pp[0] + ":" | p.upper() | header, p', ['PYTHON', 'a.py','b.py']),
			['PYTHON: A.PY', 'PYTHON: B.PY'])
