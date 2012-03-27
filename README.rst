piep
====

Bringing the power of python to stream editing
----------------------------------------------

``piep`` (pronounced "pipe") is a command line utility in the spirit of ``awk``, ``sed``, ``grep``, ``tr``, ``cut``, etc. Those tools work really well, but you have to use them a lot to keep the wildly varying syntax and options for each of them fresh in your head. If you already know python syntax, you should find ``piep`` much more natural to use.

quickstart
----------

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
 - if the output of a pipeline is a tuple, it will be joined together and printed. The default join string is " ", but this can be changed with ``--join``.
 - if the result of any linewise expression is a boolean or ``None``, it acts as a filter for that line (like ``grep``)

file-mode expressions
---------------------

Most of the expressions you'll use are linewise (those using only ``p`` and ``i``). If you use ``pp``, the operation happens on the entire stream. Note that the stream is read in lazily, so it should be considered to be an *iterator* rather than a list. However, many list-like operations are supported::

  # `head`
  $ piep 'pp[:10]'

  # `tail`
  $ piep 'pp[-10:]'

  # remove leading and trailing lines, then uppercase the rest:
  $ piep 'pp[1:-1] | p.upper()'


running shell commands
----------------------

``piep`` has a useful way of running commands on your input: the ``sh`` function. It takes multiple arguments, and each becomes a single argument to the underlying command. This means you do *not* need to quote spaces or other special shell metacharacters, so there will be no painful surprises there.

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

utility methods
---------------

There are three places where utility methods live in piep: globals, line methods (methods of ``p``) and stream methods (methods of ``pp``):

##TODO: document util methods

re-aligning input
-----------------
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

  $ echo "/bin" | piep 'sh("ls", p) | pp.flatten() | pp[:5] | " #", p'
  # bash
  # bunzip2
  # busybox
  # bzcat
  # bzcmp

Without the flatten, you would instead see output like::

  $ echo "/bin" | piep 'sh("ls", p) | pp[:5] | " #", p'
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


history / assignments
---------------------

It can be useful to reference an earlier result in the pipeline. The only non-expression allowed is a single assignment, which will capture the value of the line at that point in the pipeline. For example::

  $ echo -e "a.py\nb.py\nc.py" | piep 'orig = p | p.extonly() | orig, "is a", p, "file"'

Note that you could accomplish the same by capturing some variant of ``p`` without changing it, like so::

  $ echo -e "a.py\nb.py\nc.py" | piep 'ext = p.extonly() | p, "is a", ext, "file"'

Note that any file-mode expressions (those mentioning ``pp``) will cause previously-bound variables to go out of scope, since it would be very hard to correlate these values (and I don't really see a use for this). Typically, you'll want to modify ``pp`` before you start the line-wise expressions so it shouldn't often be a problem in practice.

extensibility
-------------

``piep`` is extensible - it's just python. You can use the ``-m``/``--import`` flag to make modules available, or pass more complicated expressions to ``--eval``. Future work will allow you to write simple plugins that extend ``piep``.

thanks
------

``piep`` was inspired by (and took a little code from) pyp_. Originally it started as an experiment to add proper (lazy) stream-based editing, and grew from there.

.. _pyp: http://code.google.com/p/pyp/
