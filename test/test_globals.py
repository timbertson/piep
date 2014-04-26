from test.test_helper import run
from unittest import TestCase
import subprocess

class TestGlobals(TestCase):
	def test_len(self):
		self.assertEqual(
			run('len(pp)', [1,2,3]), ['3'])


class TestShellCommands(TestCase):
	def test_simple_shell_commands(self):
		self.assertEqual(
			run('sh(*shellsplit(p))', ['echo "1   2 3"', 'echo 1   2 3']),
			['1   2 3', '1 2 3']
		)

	def test_shell_failures_are_tracked(self):
		self.assertRaises(subprocess.CalledProcessError, lambda: run('sh("false")', ['1']))

	def test_spawn_failures_are_tracked(self):
		self.assertRaises(subprocess.CalledProcessError, lambda: run('spawn("false")', ['1']))

	def test_shell_failures_are_suppressed(self):
		self.assertEqual(
			run('sh("false") or "failed"', ['1']),
			['failed'])

	def test_shell_failures_are_not_suppressed_with_and(self):
		self.skipTest("not implementable?")
		self.assertRaises(subprocess.CalledProcessError, lambda: run('sh("false") and "ok"', ['1']))

	def test_shell_failures_are_not_suppressed_when_explicitly_checked(self):
		self.assertRaises(subprocess.CalledProcessError, lambda: run('sh("false", check=True) or "ok"', ['1']))

	def test_shell_boolean_is_respected(self):
		self.assertEqual(run('sh("true") and "ok"', ['1']), ['ok'])

	def test_shell_combination(self):
		self.assertEqual(run('sh("false") or sh("echo", "true")', ['1']), ['true'])

	def test_shell_coercion_to_string(self):
		self.assertEqual(run('sh("echo", p) | "oo" in p', ['foo', 'bar', 'boo']), ['foo', 'boo'])
		self.assertEqual(run('sh("echo", p) | p > "doo"', ['foo', 'bar', 'boo']), ['foo'])
		self.assertEqual(run('sh("echo", p) | p[1] == "o"', ['foo', 'bar', 'boo']), ['foo', 'boo'])
		self.assertEqual(run('sh("echo", p) | p + "o"', ['foo', 'bar', 'boo']), ['fooo', 'baro', 'booo'])
		self.assertEqual(run('sh("echo", "%s", p) | p % "1"', ['foo', 'bar', 'boo']), ['1 foo', '1 bar', '1 boo'])
		self.assertEqual(run('sh("echo", p) | p * 2', ['foo', 'bar', 'boo']), ['foofoo', 'barbar', 'booboo'])

	def test_shell_short_circuiting(self):
		self.assertEqual(run('sh("echo", p) or str(sh("false"))', ['1']), ['1'])

	def test_shell_in_pipes(self):
		self.assertEqual(run('sh("echo", p) | "%s) %s" % (i, p)', ['a']), ['0) a'])
	
	def test_spawn(self):
		self.assertEqual(run('spawn("echo", "hello")', ['a']), ['a'])
	
	def test_concat(self):
		self.assertEqual(run('sh("echo", p) + p', ['a']), ['aa'])

	def test_shell_failure_in_pipes(self):
		self.assertRaises(subprocess.CalledProcessError, lambda: run('sh("false") | "%s) %s" % (i, p)', ['a']))

	def test_shell_failure_when_result_is_not_used(self):
		self.assertRaises(subprocess.CalledProcessError, lambda: run('sh("false") | "ok"', ['a']))

	def test_suppress_failures_explicitly(self):
		self.assertEqual(run('sh("false", check=False) | "ok"', ['a']), ['ok'])
	
	def test_shell_attributes_that_dont_exist_cause_coercion_to_str(self):
		self.assertEqual(run('sh("echo", p).upper()', ['a']), ['A'])

