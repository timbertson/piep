#!/usr/bin/env python

from __future__ import print_function
import os, sys
import ast
from optparse import OptionParser
import itertools

from piep.sequence import Stream, BaseList, List
from piep.line import Line
from piep.builtins import builtins
from piep.error import Exit

from .pycompat import *

DEBUG = False
def debug(*a):
	if not DEBUG: return
	print(*a)

def main(argv=None):
	if argv is None:
		argv = sys.argv[1:]
	try:
		opts, args = parse_args(argv)
		lines = run(opts, args)
		print_results(lines, opts)
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
		if isinstance(e, (AttributeError, KeyError, AssertionError, IndexError)):
			# these ones don't have very good error messages:
			e = "%s: %s" % (type(e).__name__, e)
		print(str(e), file=sys.stderr)
		sys.exit(1)

def parse_args(argv=None):
	global DEBUG
	if argv is None: argv = sys.argv[1:]
	p = OptionParser('usage: piep [OPTIONS] PIPELINE')
	p.add_option('--debug', action='store_true')
	p.add_option('-j', '--join', default=' ')
	p.add_option('-e', '--eval', action='append', dest='evals', default=[], metavar='EVAL', help='evaluate arbitrary code before running the script (in global scope, may be given multiple times)')
	p.add_option('-m', '--import', action='append', dest='imports', default=[], metavar='MODULE', help='add a module to global scope (may be given multiple times)')
	p.add_option('-f', '--file', action='append', dest='files', default=[], metavar='FILE', help='add another input stream (available as files[n])')
	p.add_option('-i', '--input', dest='input', help='use a named file (instead of stdin)')
	p.add_option('-p', '--path', action='append', dest='import_paths', default=[], help='add a location to the import path (the same as $PYTHONPATH / sys.path)')
	p.add_option('-0', '--read0', action='store_true', dest='input_nullsep', help='read input as null-separated fields')
	p.add_option('-n', '--no-input', action='store_true', help='don\'t read stdin - self-constructing pipeline')
	p.add_option('--print0', action='store_true', dest='output_nullsep', help='print output as null-separated fields')
	opts, args = p.parse_args(argv)
	assert len(args) > 0, "Not enough arguments\n" + p.format_help()
	assert len(args) == 1, "Too many arguments\n" + p.format_help()
	DEBUG = opts.debug
	return (opts, args)

def print_results(lines, opts):
	'''print lines separated by either \n or \0'''
	lines = iter(lines)
	print_line = print
	if opts.output_nullsep:
		try:
			line = next(lines)
		except StopIteration:
			return
		print(line, end='')
		def print_line(line):
			print('\0', line, end='', sep='')
	for line in lines:
		print_line(line)

def run(opts, args):
	cmd = args[0]
	input_file = open(opts.input) if opts.input else sys.stdin

	opts.join = opts.join.encode('utf-8').decode('unicode_escape')

	bindings = init_globals(opts, input_file)

	debug("Pipeline string: %s" % (cmd,))
	exprs = split_on_pipes(cmd)
	debug("Split expressions:\n  - " + "\n  - ".join(exprs))
	assert len(exprs) > 0, "You must provide at least one expression"
	if opts.no_input:
		first_expr = parse_expr(exprs[0])
		if isinstance(first_expr, ast.Assign):
			assigned_names = [name.id for name in first_expr.targets]
			assert 'pp' in assigned_names, "The first expression must assign to `pp` when --no-input is specified"
		else:
			exprs[0] = 'pp=' + exprs[0]
	output = eval_pipes(exprs, bindings)

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
				if isinstance(line, (tuple, list)):
					line = opts.join.join(map(str, line))
				yield line

def init_globals(opts, input_file):
	def make_stream(f):
		return Stream(map(lambda x: Line(x.rstrip('\n\r')), iter(f)))

	pp = make_stream(input_file)
	globs = builtins.copy()
	globs['pp'] = pp
	for path in opts.import_paths:
		path = os.path.abspath(path)
		if path not in sys.path:
			sys.path.insert(0, path)
	for import_mod in opts.imports:
		import_node = ast.Import(names=[ast.alias(name=import_mod, asname=None)])
		code = compile(ast.fix_missing_locations(ast.Module(body=[import_node])), 'import %s' % (import_mod,), 'exec')
		eval(code, globs)
	for eval_str in opts.evals:
		try:
			execfn(eval_str, globs)
		except SyntaxError as e:
			raise Exit("got error: %s\nwhile evaluating: %s" % (e,eval_str))
	files = [make_stream(open(f)) for f in opts.files]
	globs['files'] = files
	if len(files) > 0: # convenience for single file operation
		globs['ff'] = files[0]
	return globs


def split_on_pipes(cmds):
	r'''
	splits total commmand array based on pipes taking into account quotes,
	parentheses and escapes. returns array of commands that will be processed procedurally.

	>>> split_on_pipes("a | b | c")
	['a', 'b', 'c']

	>>> split_on_pipes(r"a | (b|'\\') | d")
	['a', "(b|'\\\\')", 'd']

	>>> split_on_pipes("""a | b'"' | d'"'""")
	['a', 'b\'"\'', 'd\'"\'']

	>>> split_on_pipes('a | "(b|c" | d')
	['a', '"(b|c"', 'd']

	>>> split_on_pipes('a[1|2] | b')
	['a[1|2]', 'b']

	>>> split_on_pipes('{"x": 1|2} | b')
	['{"x": 1|2}', 'b']

	>>> split_on_pipes('{"x": (1)|2} | b')
	['{"x": (1)|2}', 'b']

	>>> split_on_pipes(r'a.replace("/", "\\") | b')
	['a.replace("/", "\\\\")', 'b']
	'''
	
	OPENERS = frozenset(('{', '(', '['))
	CLOSERS = {
		'}':'{',
		')':'(',
		']':'[',
	}
	QUOTES = frozenset(('"',"'"))

	cmd_array = []
	letters = list(cmds)

	cmd = ''
	escape = False
	context = []
	while letters:
		letter = letters.pop(0)
		open_ctx = context[-1] if context else None
		debug("got letter %r, open_ctx = %r, esc=%s" % (letter, open_ctx, escape))

		if not escape:
			# behave differently if inside quotes
			if open_ctx in QUOTES:
				if open_ctx == letter:
					context.pop()
			else:
				# quotes and brackets can nest in anything but quotes
				if letter in QUOTES or letter in OPENERS:
					context.append(letter)
				elif letter in CLOSERS:
					opener = CLOSERS[letter]
					if open_ctx == opener:
						context.pop()

			if letter == '|' and open_ctx is None:
				cmd_array.append(cmd.strip())
				cmd = ''
				continue

		cmd += letter

		# if backslash, set `escape` for the next letter we encounter,
		# note that two backslashes in a row reverts to unescaped
		escape = letter == '\\' and not escape

	cmd_array.append(cmd.strip())
	return cmd_array

class Mode(object):
	__slots__ = ['desc', 'vars']
	def __init__(self, desc, vars):
		self.desc = desc
		self.vars = vars
	def __str__(self): return self.desc
	def __repr__(self): return "<# mode: %s>" % (self,)

class Modes(object):
	__slots__ = ['GLOBAL', 'LINE']
	def __init__(self):
		self.GLOBAL = Mode('global', set(['pp','files','ff']))
		self.LINE = Mode('line', set(['p', 'i']))
MODE = Modes()
RESERVED_VARS = MODE.GLOBAL.vars.union(MODE.LINE.vars)
NON_ASSIGNABLE_VARS = RESERVED_VARS.difference(['pp', 'p'])

def detect_mode(expr, source_text):
	names = set()
	class NameFinder(ast.NodeVisitor):
		def visit_Assign(self, node):
			assigned_names = set(name.id for name in node.targets if isinstance(name, ast.Name))
			reserved_names = list(assigned_names.intersection(NON_ASSIGNABLE_VARS))
			if reserved_names:
				raise AssertionError("can't assign to `%s` (expression: %s)" % (sorted(reserved_names)[0], source_text))
			names.update(assigned_names)
			self.generic_visit(node)

		def visit_Name(self, node):
			if isinstance(node.ctx, ast.Load):
				names.add(node.id)
			self.generic_visit(node)
	NameFinder().visit(expr)
	debug('expr references: %r' % (names,))

	mode = None
	if len(names.intersection(MODE.GLOBAL.vars)) > 0:
		mode = MODE.GLOBAL

	if len(names.intersection(MODE.LINE.vars)) > 0:
		assert mode is None, "Can't use file-level and line-level expressions in the same pipe expression: " + source_text
		mode = MODE.LINE
	return (mode or MODE.LINE), names

def parse_expr(expr):
	try:
		return ast.parse(expr + '\n', mode='eval').body
	except SyntaxError as e:
		try:
			stmt = ast.parse(expr + '\n', mode='exec').body
			if len(stmt) == 1 and isinstance(stmt[0], ast.Assign):
				# single assignments are OK
				return stmt[0]
			else:
				raise e
		except SyntaxError as e:
			raise Exit("got error: %s\nwhile evaluating: %s" % (e,expr))

def compile_pipe_exprs(exprs):
	body = []

	# this code doesn't need to be parameterised, so we'll just parse a string
	post_pipe_check = ast.parse(
			"_check_for_failed_commands()\n"
		).body
	post_expr_check = post_pipe_check + ast.parse(
			"if callable(_p): _p = _p(p)\n"
			"p = p if _p is True else (None if _p is False else _p)\n"
			"if p is None: return None\n"
		).body

	def annotate(expr):
		'''get the mode & referenced variables for a given ast node'''
		ast_node = parse_expr(expr)
		mode, vars = detect_mode(ast_node, expr)
		return ast_node, mode, vars

	def name(id, ctx=None):
		if ctx is None:
			ctx = ast.Load()
		return ast.Name(id=id, ctx=ctx)

	if is_python_2:
		arg = name
	else:
		def arg(id):
			return ast.arg(id, None)

	def assign(var, expr):
		return ast.Assign(targets=[name(var, ctx=ast.Store())], value=expr)

	def combine_pipe_transforms(body):
		'''
		Takes a list of expressions and creates a list of statements
		to process the entirety of ``pp`` with the given sub-pipeline.
		Importantly, the expressions exist in the same lexical scope, so
		assignments are available for use in subsequent expressions.
		'''
		transform_def = ast.FunctionDef(
			name='_transformer',
			args=ast.arguments(
				args=[arg('p'), arg('i')],
				vararg=None,
				kwarg=None,
				kwonlyargs=[],
				kw_defaults=[],
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
			func=name('_ensure_piep_sequence'),
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

	#raise RuntimeError(ast.dump(mod))
	return compile(mod, '(input)', 'exec')

def eval_pipes(exprs, bindings):
	mod = compile_pipe_exprs(exprs)
	execfn(mod, bindings)
	return bindings['pp']

if __name__ == '__main__':
	main()
