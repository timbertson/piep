piep
====

.. image:: http://gfxmonk.net/dist/status/project/piep.png

Bringing the power of python to stream editing
----------------------------------------------

``piep`` (pronounced "pipe") is a command line utility in the spirit of ``awk``, ``sed``, ``grep``, ``tr``, ``cut``, etc. Those tools work really well, but you have to use them a lot to keep the wildly varying syntax and options for each of them fresh in your head. If you already know python syntax, you should find ``piep`` much more natural to use.

It's released under the GPLv3 licence (see the LICENCE file).

| Online documentation:
| http://gfxmonk.net/dist/doc/piep/

| Source Code / Issues:
| https://github.com/gfxmonk/piep/

| Pypi:
| http://pypi.python.org/pypi/piep


Quickstart
-----------

``piep`` usually takes a single argument, the pipeline. This is a series of python expressions, separated by pipes. The important variables to know about are ``p`` (the current line), ``pp`` (the entire input) and sometimes ``i`` (the index of the current line). The result of each expression becomes ``p`` in the next part of the pipeline.

The pipeline is run over the program's input (``stdin``, or the file provided with ``-i``/``--input``).

Here's a few examples to give you an idea::

  $ echo -e "Here are\nsome\nwords for you." | piep 'p.split() | len(p)'
  2
  1
  3

  $ echo -e "1\n2\n3\n4\n5\n6" | piep 'int(p) | p % 2 == 0 | p , "is even!"'
  2 is even!
  4 is even!
  6 is even!

Things to note:

 - The argument to ``piep`` needs to be surrounded with quotes (otherwise your shell would try and interpret the spaces, pipes, brackets etc). Single quotes are best, to prevent any interference from the shell.
 - ``p`` is not always a string. In the first example we broke apart each line into a list using ``split``, and then that list became the next value of ``p``. It could instead be written as::

      $ piep 'len(p.split())'

   But that gets messy when we get into complicated pipelines (and makes for lots of brackets).
 - if the output of a pipeline is a list or tuple, it will be joined together and printed. The default join string is " ", but this can be changed with ``--join``.
 - if the result of any linewise expression is a boolean or ``None``, it acts as a filter for that line (like ``grep``)
 - if the result of any linewise expression is a callable object, it will be passed the current value of ``p`` to form the new value of ``p``. This makes it easy to chain functions by just mentioning them, e.g::

      $ echo -e '1\n2\n3' | piep 'int | [p, p + 1] | pretty'

   (here ``int`` is treated as ``int(p)`` and ``pretty`` is treated as ``pretty(p)``). If you need to assign a function to the value of ``p`` without having it invoked, you can so do explicitly: ``p = str``.

File-mode expressions
----------------------

Most of the expressions you'll use are linewise (those using only ``p`` and ``i``). If you use ``pp``, the operation happens on the entire stream. Note that the stream is read in lazily and cannot be "rewound", so it should be considered to be an *iterator* rather than a list. However, it does support some of the same operations::

  # `head`
  $ piep 'pp[:10]'

  # `tail`
  $ piep 'pp[-10:]'

  # remove leading and trailing lines, then uppercase the rest:
  $ piep 'pp[1:-1] | p.upper()'

.. warning::
	Slice syntax is supported, but is destructive and will mutate the ``pp`` iterator, so complex expressions involving slicing or indexing may have surprising results. I'm interested in improving this, but for now if you try anything *too* fancy with ``pp``, it may not work as expected.

On the plus side, even slice operations are as lazy as they can be - if your slice only needs to read the first 10 lines in the input, that's all that will be read. This is extremely useful for testing out commands by limiting them to the first few lines of a big file.

.. tip::
	If you need to treat ``pp`` as a regular (non-destructively-updating) list, you can force it by starting your pipeline with ``list(pp) | ...``. That way, ``pp`` will be eagerly read in and treated as a list instead of a stream. Obviously, this will have adverse affects on memory usage for large input files.

.. note::
	You'll get an error if you try to use both file-level objects (like ``pp``) and line-level objects (like ``p``) in a *single* expression. You can still use a mixture of file and line-level expressions, just as long as they are separated by pipes.

Additional file inputs
----------------------

If you use the ``-f/--file`` option, you get additional inputs. You can pass this option multiple times, and each file will be read in as a lazy stream with the same functionality as ``pp``. These files are available as the ``files`` list. There aren't many use cases for this yet, but one is iterating over pairs of items (one from stdin, one from a file) in concert::

  $ piep --file=input2 'pp.zip(files[0]) | "STDIN:%s\tINPUT:%s" % p'

If you only want to use one additional file, you can use the convenient alias ``ff`` instead of ``files[0]`` to reference it.

.. _running shell commands:

Running shell commands
-----------------------

``piep`` has a simple way of running commands on your input: the ``sh`` function. It takes multiple arguments, and each becomes a single argument to the underlying command. This means you do *not* need to quote spaces or other special shell metacharacters, so there will be no painful surprises there.

::

  $ echo -e "setup.py\nMakefile" | piep 'sh("wc", "-l", p)'

The output of ``sh`` is whatever the command prints.

If you wish to run a command without using the output, you can use the ``spawn`` function instead. This acts just like ``sh``, except the output is ignored and the expression returns
``True`` (which will maintain the existing value of ``p`` in a pipeline)::

  $ ls -1 | piep 'spawn("touch", p) | "Touched: " + p'


If you still want to see the command output printed without it becoming part of the pipeline, you can pass ``stdout=None`` to suppress the default redirection.

If a command fails (when using from either ``sh`` or ``spawn``), an exception will be raised telling you so::

  $ echo -e "setup.py\nMakefile" | piep 'sh("false")'
  Command 'false' returned non-zero exit status 1
  $ echo $?
  1

If you wish to suppress this behaviour, you can do so explicitly::

  $ echo -e "setup.py\nMakefile" | piep 'sh("false", check=False) + "line!"'
  line!
  line!

Or (for ``sh`` only) by coercing it to a boolean - it is assumed that if you use a command as a boolean, you will be managing failures yourself::

  $ echo -e "echo ok\nfalse" | piep 'p.split() | sh(*p) or "(failed)"'
  ok
  (failed)


If you absolutely must use shell syntax, you can pass the keyword argument ``shell=True``.

Utility methods
----------------

There are three places where utility methods live in piep: globals, line methods (methods of ``p``) and stream methods (methods of ``pp``):

Methods available on `p` (an input line)
++++++++++++++++++++++++++++++++++++++++

.. autoclass:: piep.line.Line
  :members:

Methods available on `pp` (the input stream)
++++++++++++++++++++++++++++++++++++++++++++

.. autoclass:: piep.list.BaseList
  :members:

Global functions / variables
++++++++++++++++++++++++++++

The contents of ``piep.builtins`` is mixed in to the global scope, so all of the following are available unqualified:

.. automodule:: piep.builtins
  :members:

Re-aligning input
------------------

When an expression based on one input line generates multiple lines (or a sequence), future expressions will use that multi-line string or sequence as the new value of ``p``. If you want to roll up a *sequence* back into ``pp``, use ``pp.merge()``. To flatten a multi-line string, use ``pp.flatten()``.

Take this example::

  $ echo -e "2\n4" | piep 'int(p) | range(0, p) | repr(p)'
  [0, 1]
  [0, 1, 2, 3]

If you wanted each number to come on its own line (for formatting's sake, or for further processing), you can use ``merge``::

  $ echo -e "2\n4" | piep 'int(p) | range(0, p) | pp.merge()'
  0
  1
  0
  1
  2
  3

The same can be done for multi-line strings, with ``flatten``::

  $ echo "/bin" | piep 'sh("ls", p) | pp.flatten() | pp[:5] | "#", p'
  # bash
  # bunzip2
  # busybox
  # bzcat
  # bzcmp

Without the flatten, you would instead see output like::

  $ echo "/bin" | piep 'sh("ls", p) | pp[:5] | "#", p'
  # bash
  bunzip2
  busybox
  bzcat
  bzcmp
  bzdiff
  bzegrep
  bzexe
  bzfgrep
  bzgrep
  bzip2
  ( ... )


History / Variable Assignments
------------------------------

It can be useful to reference an earlier result in the pipeline. The only non-expression allowed is a single assignment, which will capture the value of the line at that point in the pipeline. For example::

  $ echo -e "a.py\nb.py\nc.py" | piep 'orig = p | p.extonly() | orig, "is a", p, "file"'
  a.py is a py file
  b.py is a py file
  c.py is a py file

Note that you could accomplish the same by capturing some variant of ``p`` without changing it, like so::

  $ echo -e "a.py\nb.py\nc.py" | piep 'ext = p.extonly() | p, "is a", ext, "file"'

Note that any file-mode expressions (those mentioning ``pp``) will cause previously-bound variables to go out of scope, since it would be very hard to correlate these values (and I don't really see a use for this). Typically, you'll want to modify ``pp`` before you start the line-wise expressions so it shouldn't often be a problem in practice.

Extensibility
--------------

``piep`` is extensible - it's just python. You can use the ``-m``/``--import`` flag to make modules available, or pass more complicated expressions to ``--eval``. Future work will allow you to write simple plugins that extend ``piep``.

Changes
-------

0.6:
  - cleaned up & documented ``--file`` functionality
  - fix incorrect ``repr`` for shell results
  - add the ability to explicitly check the result of shell commands, even when they are coerced into a boolean
  - add ``pp.sort``, ``pp.sortby``, ``pp.uniq``

0.7:
  - added ``Line.reverse()``
  - add a bunch of shell coersion operators
  - add ``--no-input`` (self-constrcting pipeline) mode
  - add ``--print0`` mode to separate output records with the null byte

0.8:
  - bug fixes, particularly parsing edge cases (thanks Matt Giuca)
  - add ``spawn()``, ``devnull`` and ``ignore()`` builtins
  - auto-invocation of pipeline expressions that return functions - i.g. ``str`` now evaluates to ``str(p)``

Thanks
-------

``piep`` was inspired by (and took a little code from) pyp_. Originally it started as an experiment to add proper (lazy) stream-based editing, and grew from there.

.. _pyp: http://code.google.com/p/pyp/
