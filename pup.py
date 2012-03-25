#!/usr/bin/env python

from __future__ import print_function
import os, sys
import ast
from optparse import OptionParser
import itertools
import lazy_list

DEBUG = False
def debug(*a):
	if not DEBUG: return
	print(*a)

def main():
	global DEBUG
	p = OptionParser()
	p.add_option('--debug', action='store_true')
	opts, args = p.parse_args()
	DEBUG = opts.debug

	assert len(args) > 0
	cmd = args[0]
	additional_files = args[1:]
	#TODO: something with additional_files!

	exprs = split_on_pipes(cmd)
	debug("Split expressions: " + "\n".join(exprs))
	piped_exprs = [ast.parse(cmd.strip() + '\n', mode='eval').body for cmd in exprs]
	output = eval_pipes(piped_exprs)

	# strings are iterable, but we don't want to do that!
	if isinstance(output, basestring):
		output = [output]
	try:
		output = iter(output)
	except TypeError as err:
		debug(err)
		print(output)
	else:
		for line in output:
			if line is not None:
				print(line)

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

from line import Line
def eval_pipes(exprs):
	pp = lazy_list.LazyList(itertools.imap(lambda x: Line(x.rstrip('\n\r')), iter(sys.stdin)))
	for expr in exprs:
		if not isinstance(pp, lazy_list.LazyList):
			# if the last expr turned pp into a normal list or some other iterable, fix that...
			pp = lazy_list.LazyList(iter(pp))
		expr_globals = {'pp': pp}
		mode = detect_mode(expr)
		if mode == MODE.LINE:
			expr = make_linewise_transform(expr)

		# compile() wants an expr at the top level
		if not isinstance(expr, ast.Expr):
			expr = ast.Expression(expr)

		# and lots of other stuff
		ast.fix_missing_locations(expr)

		expr = compile(expr, '(input)', 'eval')
		pp = eval(expr, expr_globals)
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
