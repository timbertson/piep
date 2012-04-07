import sys
import itertools

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

