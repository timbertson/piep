import os
import sys
import itertools
import contextlib
import shutil
import tempfile

from piep import main

def run(*args):
	args = list(args)
	stdin = itertools.imap(str, args.pop())
	old_stdin = sys.stdin
	try:
		sys.stdin = stdin
		return [str(line) for line in main.run(args)]
	finally:
		sys.stdin = old_stdin

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
