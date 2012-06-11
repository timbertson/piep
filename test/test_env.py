from test.test_helper import run, temp_cwd
from unittest import TestCase
import subprocess


class TestModuleImporting(TestCase):
	def test_modules_are_not_importable_from_cwd_by_default(self):
		# for the same reason $PATH does not include
		# "." - it could be an attack vector
		with temp_cwd():
			with open("mymod.py", 'w') as f:
				f.write("def up(s): return s.upper()")
			self.assertRaises(ImportError,
				lambda: run('-m', 'mymod', 'mymod.up(p)', ['a']))

	def test_modules_can_be_imported_from_cwd(self):
		with temp_cwd():
			with open("mymod.py", 'w') as f:
				f.write("def up(s): return s.upper()")
			self.assertEqual(
				run('-p', '.', '-m', 'mymod', 'mymod.up(p)', ['a']), ['A'])

