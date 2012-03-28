#!/usr/bin/env python

from __future__ import print_function
import os, sys
import ast
from optparse import OptionParser
import itertools

from piep.list import Stream, BaseList, List
from piep.line import Line
from piep.builtins import builtins
from piep.error import Exit

if sys.version_info < (3,):
	imap = itertools.imap
else:
	imap = map

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
	except Exception as e:
		if DEBUG:
			import traceback
			traceback.print_exc(file=sys.stderr)
		print(str(e), file=sys.stderr)
		sys.exit(1)

def run(argv=None):
	global DEBUG
	if argv is None: argv = sys.argv[1:]
	p = OptionParser('usage: %prog [OPTIONS] <expr> [additional_files ...]')
	p.add_option('--debug', action='store_true')
	p.add_option('-j', '--join', default=' ')
	p.add_option('-e', '--eval', action='append', dest='evals', default=[], metavar='EVAL', help='evaluate arbitrary code before running the script (in global scope, may be given multiple times)')
	p.add_option('-m', '--import', action='append', dest='imports', default=[], metavar='MODULE', help='add a module to global scope (may be given multiple times)')
	p.add_option('-f', '--file', action='append', dest='files', default=[], metavar='FILE', help='add another input file (available as f[n])')
	p.add_option('-i', '--input', dest='input', help='use a named file (instead of stdin)')
	opts, args = p.parse_args(argv)
	DEBUG = opts.debug

	assert len(args) == 1, "Please provide exactly one argument"
	cmd = args[0]
	input_file = open(opts.input) if opts.input else sys.stdin

	opts.join = opts.join.decode('string_escape')
	# bytes(myString, "utf-8").decode("unicode_escape") # python3

	bindings = init_globals(opts, input_file)

	exprs = split_on_pipes(cmd)
	debug("Split expressions: " + "\n".join(exprs))
	def compile_expr(expr):
		try:
			return ast.parse(cmd.strip() + '\n', mode='eval').body
		except SyntaxError as e:
			try:
				stmt = ast.parse(cmd.strip() + '\n', mode='exec').body
				if len(stmt) == 1 and isinstance(stmt[0], ast.Assign):
					# single assignments are OK
					return stmt[0]
				else:
					raise e
			except SyntaxError as e:
				raise Exit("got error: %s\nwhile evaluating: %s" % (e,expr))

	piped_exprs = [compile_expr(cmd) for cmd in exprs]
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

def init_globals(opts, input_file):
	def make_stream(f):
		return Stream(imap(lambda x: Line(x.rstrip('\n\r')), iter(f)))

	pp = make_stream(input_file)
	globs = builtins.copy()
	globs['pp'] = pp
	for import_mod in opts.imports:
		import_node = ast.Import(names=[ast.alias(name=import_mod, asname=None)])
		code = compile(ast.fix_missing_locations(ast.Module(body=[import_node])), 'import %s' % (import_mod,), 'exec')
		eval(code, globs)
	for eval_str in opts.evals:
		try:
			exec eval_str in globs
		except SyntaxError as e:
			raise Exit("got error: %s\nwhile evaluating: %s" % (e,eval_str))
	globs['f'] = [make_stream(open(f)) for f in opts.files]
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
	#found_vars = important_vars.intersection(names)
	#if len(found_vars) > 1:
	#	raise RuntimeError("ambiguous expression uses too many variables!")

	mode = MODE.LINE
	if 'pp' in names:
		mode = MODE.GLOBAL
	return mode, names



def compile_pipe_exprs(exprs):
	body = []

	# this check between each expr doesn't need to be parameterised, so we'll just parse a string
	post_pipe_check = ast.parse(
			"_check_for_failed_commands()\n"
		).body
	post_expr_check = post_pipe_check + ast.parse(
			"p = p if _p is True else (None if _p is False else _p)\n"
			"if p is None: return None\n"
		).body
	
	def annotate(expr):
		mode, vars = detect_mode(expr)
		return expr, mode, vars

	def name(id, ctx=None):
		if ctx is None:
			ctx = ast.Load()
		return ast.Name(id=id, ctx=ctx)

	def assign(var, expr):
		return ast.Assign(targets=[name(var, ctx=ast.Store())], value=expr)

	def combine_pipe_transforms(body):
		transform_def = ast.FunctionDef(
			name='_transformer',
			args=ast.arguments(
				args=[name('p'), name('i')],
				vararg=None,
				kwarg=None,
				defaults=[]
			),
			body=body + [ast.Return(name('p'))],
			decorator_list=[])

		map_fn = ast.Attribute(value=name('pp'), attr='map_index', ctx=ast.Load())
		assign_pp = assign('pp', ast.Call(
				func=map_fn,
				args=[name('_transformer')],
				keywords=[],
				starargs=None,
				kwargs=None
				))
		return [
			transform_def,
			assign_pp
			]

	annotated_exprs = map(annotate, exprs)
	is_linewise = lambda x: x[1] is MODE.LINE

	def ensure_stream():
		call = ast.Call(
			func=name('_ensure_stream'),
			args=[name('pp')],
			keywords=[],
			starargs=None,
			kwargs=None
		)
		body.append(assign('pp', call))

	for linewise, group in itertools.groupby(annotated_exprs, is_linewise):
		if linewise:
			group_body = []
			for item in group:
				expr, mode, vars = item
				if not isinstance(expr, ast.Assign):
					group_body.append(assign('_p', expr))
					group_body.extend(post_expr_check)
				else:
					group_body.append(expr)
			ensure_stream()
			body.extend(combine_pipe_transforms(group_body))
		else:
			for item in group:
				expr = item[0]
				ensure_stream()
				if not isinstance(expr, ast.Assign):
					expr = assign('pp', expr)
				body.append(expr)
				body.extend(post_pipe_check)
	
	mod = ast.Module(body=body)
	ast.fix_missing_locations(mod)

	#import codegen
	#raise RuntimeError(codegen.to_source(mod))
	#raise RuntimeError(ast.dump(mod))
	return compile(mod, '(input)', 'exec')

def eval_pipes(exprs, bindings):
	# and lots of other stuff
	mod = compile_pipe_exprs(exprs)
	exec mod in bindings
	debug("after pipe, pp = %r" % (bindings['pp'],))
	return bindings['pp']

def make_linewise_transform(expr, vars):
	input_args = [ast.Name(id='p', ctx=ast.Load())]
	method_name = 'map'
	debug("making linewise expr that uses the following vars: %r" % (vars,))

	if 'i' in vars:
		input_args.append(ast.Name(id='i', ctx=ast.Load()))
		method_name = 'map_index'

	transformer = ast.Lambda(
		args=ast.arguments(
			args=input_args,
			vararg=None,
			kwarg=None,
			defaults=[]
		),
		body=expr)
	map_fn = ast.Attribute(value=ast.Name(id='pp', ctx=ast.Load()), attr=method_name, ctx=ast.Load())
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
