import os
import sys
import itertools
import contextlib
import shutil
import tempfile
import subprocess

from piep import main

def run(*args):
	args = list(args)
	stdin = itertools.imap(str, args.pop())
	old_stdin = sys.stdin
	try:
		sys.stdin = stdin
		return [str(line) for line in main.run(*main.parse_args(args))]
	finally:
		sys.stdin = old_stdin

def run_full(*args):
	args = list(args)
	stdin = args.pop()
	proc = subprocess.Popen([sys.executable, '-m', 'piep'] + args,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE,
		env={
			'PYTHONPATH': os.path.dirname(os.path.dirname(main.__file__))
		}
	)
	out, err = proc.communicate(stdin)
	if proc.returncode != 0:
		raise AssertionError("Command failed\nout: %s\nerr: %s" % (out, err))
	return out


@contextlib.contextmanager
def cwd(path):
	old_cwd = os.getcwd()
	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(old_cwd)

@contextlib.contextmanager
def temp_cwd():
	path = tempfile.mkdtemp()
	try:
		with cwd(path):
			yield
	finally:
		shutil.rmtree(path)
