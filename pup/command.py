#!/usr/bin/env python

from __future__ import print_function
import os, sys
import ast
from optparse import OptionParser
import itertools

from pup.lazy_list import LazyList
from pup.line import Line

if sys.version_info < (3,):
	imap = itertools.imap
else:
	imap = map

class Exit(BaseException): pass


DEBUG = False
def debug(*a):
	if not DEBUG: return
	print(*a)

def main(argv=None):
	try:
		for line in run(argv):
			print(line)
		return 0
	except Exit as e:
		if e.message:
			print(e.message, file=sys.stderr)
		sys.exit(1)
	except KeyboardInterrupt:
		print("interrupted", file=sys.stderr)
		sys.exit(1)

def run(argv=None):
	global DEBUG
	if argv is None: argv = sys.argv[1:]
	p = OptionParser()
	p.add_option('--debug', action='store_true')
	p.add_option('-j', '--join', default=' ')
	p.add_option('-e', '--eval', action='append', dest='evals', default=[], help='evaluate something before running the script (in global scope, may be given multiple times)')
	p.add_option('--import', action='append', dest='imports', default=[], help='add a module to global scope (may be given multiple times)')
	opts, args = p.parse_args(argv)
	DEBUG = opts.debug

	assert len(args) > 0
	cmd = args[0]
	additional_files = args[1:]
	#TODO: something with additional_files!

	bindings = init_globals(opts)

	exprs = split_on_pipes(cmd)
	debug("Split expressions: " + "\n".join(exprs))
	piped_exprs = [ast.parse(cmd.strip() + '\n', mode='eval').body for cmd in exprs]
	output = eval_pipes(piped_exprs, bindings)

	# strings are iterable, but we don't want to do that!
	if isinstance(output, basestring):
		output = [output]
	try:
		output = iter(output)
	except TypeError as err:
		debug(err)
		yield output
	else:
		for line in output:
			if line is not None:
				if isinstance(line, tuple) or isinstance(line, list):
					line = opts.join.join(map(str, line))
				yield line

def init_globals(opts):
	pp = LazyList(imap(lambda x: Line(x.rstrip('\n\r')), iter(sys.stdin)))
	globs = {'pp':pp}
	for import_mod in opts.imports:
		import_node = ast.Import(names=[ast.alias(name=import_mod, asname=None)])
		code = compile(ast.fix_missing_locations(ast.Module(body=[import_node])), 'import %s' % (import_mod,), 'exec')
		eval(code, globs)
	for eval_str in opts.evals:
		try:
			exec eval_str in globs
			#eval(eval_str, globs)
			print(repr(globs.keys()))
		except SyntaxError as e:
			raise Exit("got error: %s\nwhile evaluating: %s" % (e,eval_str))
	return globs


def split_on_pipes(cmds):
	'''
	splits total commmand array based on pipes taking into account quotes,
	parentheses and escapes. returns array of commands that will be processed procedurally.

	lifted from `pyp`
	'''
	
	cmd_array = []
	cmd = ''
	open_single = False
	open_double = False
	open_parenth = 0
	escape = False
	letters = list(cmds)
	while letters:
		letter = letters.pop(0)
		if cmd and cmd[-1] == '\\': escape = True
		
		#COUNTS QUOTES
		if letter == "'":
			if open_single and not escape:
				open_single = not open_single
			else:
				open_single = True
		if letter == '"':
			if open_double and not escape:
				open_double = not open_double
			else:
				open_double = True
		
		#COUNTS REAL PARENTHESES
		if not open_single and not open_double:
			if letter == '(' :
				open_parenth = open_parenth + 1
			if letter == ')':
				open_parenth = open_parenth - 1

		if letter == '|' and not open_single and not open_double and not open_parenth:#
			cmd_array.append(cmd)
			cmd = ''
		else:
			cmd = cmd + letter
		escape = False

	cmd_array.append(cmd)
	return cmd_array

class Mode(object):
	__slots__ = ['GLOBAL', 'LINE']
	def __init__(self):
		self.GLOBAL = 'global'
		self.LINE = 'line'
MODE = Mode()

def detect_mode(expr):
	names = set()
	class NameFinder(ast.NodeVisitor):
		def visit_Name(self, node):
			names.add(node.id)
	NameFinder().visit(expr)
	important_vars = set(['pp', 'p'])
	debug('expr references: %r' % (names,))
	found_vars = important_vars.intersection(names)
	if len(found_vars) > 1:
		raise RuntimeError("ambiguous expression uses too many variables!")
	if 'pp' in found_vars:
		return MODE.GLOBAL
	if 'p' in found_vars:
		return MODE.LINE
	raise RuntimeError("unknown mode for expression that references: %r (expr = %s)" % (names, ast.dump(expr)))

def eval_pipes(exprs, bindings):
	pp = bindings['pp']
	for expr in exprs:
		if not isinstance(pp, LazyList):
			# if the last expr turned pp into a normal list or some other iterable, fix that...
			pp = LazyList(iter(pp))
		bindings['pp'] = pp
		mode = detect_mode(expr)
		if mode == MODE.LINE:
			expr = make_linewise_transform(expr)

		# compile() wants an expr at the top level
		if not isinstance(expr, ast.Expr):
			expr = ast.Expression(expr)

		# and lots of other stuff
		ast.fix_missing_locations(expr)

		expr = compile(expr, '(input)', 'eval')
		pp = eval(expr, bindings)
		debug("after pipe, pp = %r" % (pp,))
	return pp

def make_linewise_transform(expr):
	transformer = ast.Lambda(
		args=ast.arguments(
			args=[ast.Name(id='p', ctx=ast.Load())],
			vararg=None,
			kwarg=None,
			defaults=[]
		),
		body=expr)
	map_fn = ast.Attribute(value=ast.Name(id='pp', ctx=ast.Load()), attr='map', ctx=ast.Load())
	mapping = ast.Call(
			func=map_fn,
			args=[transformer],
			keywords=[],
			starargs=None,
			kwargs=None
	)
	return mapping

if __name__ == '__main__':
	main()
