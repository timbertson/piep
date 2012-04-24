piep
====

Bringing the power of python to stream editing
----------------------------------------------

``piep`` (pronounced "pipe") is a command line utility in the spirit of ``awk``, ``sed``, ``grep``, ``tr``, ``cut``, etc. Those tools work really well, but you have to use them a lot to keep the wildly varying syntax and options for each of them fresh in your head. If you already know python syntax, you should find ``piep`` much more natural to use.

It's released under the GPLv3 licence (see the LICENCE file).

| Zero install feed:
| http://gfxmonk.net/dist/0install/piep.xml

| Online documentation:
| http://gfxmonk.net/dist/doc/piep/

| Source Code / Issues:
| https://github.com/gfxmonk/piep/

| Cheese shop entry:
| http://pypi.python.org/pypi/piep


Getting it
------------
The preferred distribution method is via `Zero Install <http://0install.net/>`_. To make it available to your user as ``piep``, you should run::

  $ 0alias piep http://gfxmonk.net/dist/0install/piep.xml

If you just want to try it out and don't want to make an alias, you can run it without changing anything on your system::

  $ 0launch http://gfxmonk.net/dist/0install/piep.xml

**Note**: This requires ``zero install`` to be installed. On linux, this is usually part of the ``zeroinstall-injector`` package. Zero install is cross-platform, see `the website <http://0install.net/>`_ for installation on other platforms.

If you must, you can most likely ``pip install piep``. But that route is less well supported, as the author strongly discourages the use of language-specific platform managers, especially those as convoluted as setuptools/distutils/distribute/packaging.

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

 - The pipe character is *inside* the argument given to ``piep``, so it needs to be quoted so that the shell won't try and interpret it.
 - ``p`` is not always a string. In the first example broke apart each line into a list using ``split``, and then that list becomes the next value of ``p``. It could instead be written as::

      $ piep 'len(p.split())'

   But that gets messy when we get into complicated pipelines (and makes for lots of brackets).
 - if the output of a pipeline is a list or tuple, it will be joined together and printed. The default join string is " ", but this can be changed with ``--join``.
 - if the result of any linewise expression is a boolean or ``None``, it acts as a filter for that line (like ``grep``)

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

The output of ``sh`` is whatever the command prints. If a command fails, an exception will be raised telling you so::

  $ echo -e "setup.py\nMakefile" | piep 'sh("false")'
  Command 'false' returned non-zero exit status 1
  $ echo $?
  1

If you wish to suppress this behaviour, you can do so explicitly::

  $ echo -e "setup.py\nMakefile" | piep 'sh("false", check=False) + "line!"'
  line!
  line!

Or by coercing it to a boolean (it is assumed that if you use a command as a boolean, you will be managing failures yourself)::

  $ echo -e "echo ok\nfalse" | piep 'p.split() | sh(*p) or "(failed)"'
  ok
  (failed)

If you absolutely must use shell syntax, you can pass the keyword argument ``shell=True``. But the author strongly advises against this.

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

Thanks
-------

``piep`` was inspired by (and took a little code from) pyp_. Originally it started as an experiment to add proper (lazy) stream-based editing, and grew from there.

.. _pyp: http://code.google.com/p/pyp/
