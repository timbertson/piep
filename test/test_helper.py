import sys
import itertools

from pup import command

def run(*args):
	args = list(args)
	stdin = itertools.imap(str, args.pop())
	old_stdin = sys.stdin
	try:
		sys.stdin = stdin
		return [str(line) for line in command.run(args)]
	finally:
		sys.stdin = old_stdin

