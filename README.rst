.. image:: https://img.shields.io/travis/flowroute/ebb-lint/master.svg?style=flat-square

.. image:: https://img.shields.io/coveralls/flowroute/ebb-lint/master.svg?style=flat-square

.. image:: https://img.shields.io/pypi/v/ebb-lint.svg?style=flat-square

.. image:: https://img.shields.io/pypi/format/ebb-lint.svg?style=flat-square

.. image:: https://img.shields.io/pypi/pyversions/ebb-lint.svg?style=flat-square

.. image:: https://img.shields.io/pypi/l/ebb-lint.svg?style=flat-square


==========
 ebb-lint
==========

It's a `flake8`_ plugin!
It lints for style problems!
To activate it::

  $ pip install ebb-lint


Configuration
=============

Configuration does nothing but cause bugs or laxness,
so ``ebb-lint`` recommends keeping the defaults as-is.
However,
there are two configuration options provided for dealing with `long lines`_.
Both can be specified either
on the command line by passing flags to ``flake8``,
or with `the typical configuration methods <https://flake8.readthedocs.org/en/stable/config.html>`_.

``hard-max-line-length``
  Lines must never be longer than this value.
  The default is 119 columns.

``permissive-bulkiness-percentage``
  Lines can exceed ``max-line-length``
  (which is considered the "soft limit")
  only if the line contains greater than or equal to this percentage of string literals *or* comments,
  but the percentages of each are not combined.
  The default is 67%.
  For more detail, see the section about `long lines`_.

.. _one-off scripts:

When writing a one-off script,
to use ``print`` against ``ebb-lint``\ 's wishes,
add a comment to the top of the file to disable that warning::

  # I sincerely swear that this is one-off code.

This comment must be above any statements in the code
(including docstrings),
on a line by itself.


noqa
====

``ebb-lint`` disables ``# noqa`` comments with extreme prejudice.
The feature is over-used and over-general;
it's not possible to only mark *certain* errors as acceptable,
and as a result,
it's possible for a line marked ``noqa`` for one error to completely mask a different error.


Errors
======

All of the possible errors,
organized by category:


L1: Docstrings
--------------

L101
  The ``__init__`` method of classes must not have a docstring,
  as it is `standard sphinx style <http://sphinx-doc.org/domains.html#directive-py:class>`_ to put that information on the class docstring.

L102
  A docstring was incorrectly formatted.
  Single-line docstrings must resemble this::

    def func():
        """Spam eggs."""

  Multi-line docstrings must resemble this::

    def func():
        """
        Spam eggs.

        Also, sausage.
        """

L103
  A test docstring
  (i.e. the docstring on a function or method with a name starting with ``test_``)
  must not start with any form of the words
  "test",
  "verify",
  or "ensure".

L104
  Docstrings must use `Napoleon`_,
  not `reStructuredText fields`_.


L2: Dubious syntax
------------------

Some features of python do more harm than good.
These errors catch potential problems in situations where the programmer might have intended to do one thing,
but accidentally did something else instead.

L201
  Container literals must have a trailing comma following the last element.
  If the closing ``)``, ``]``, or ``}`` is on the same line as the last element,
  this error is not emitted.

L202
  ``print`` is not allowed except for debugging.
  For production code,
  logging is much more flexible and predictable.
  This can be disabled in `one-off scripts`_.

L203
  ``pdb`` and compatible modules
  (i.e. modules exposing a ``set_trace`` function)
  are not allowed except for debugging.
  If a ``set_trace`` call was allowed into production,
  it would likely wedge the process.

L204
  Implicit string literal concatenation
  (i.e. ``'spam' 'eggs'`` being isomorphic to ``'spameggs'``)
  is only allowed if every string being concatenated is parenthesized,
  and the parentheses contain nothing but string literals.

  This is okay::

    some_string = ('spam {} '
                   'eggs').format('spam')

  And this is not::

    some_list = [
        'spam'
        'eggs',
        'sausage',
    ]

L205
  ``__init__.py`` is not allowed to contain function or class definitions.

L206
  `Implicit relative imports`_ are not allowed.

L207
  ``pass`` is only necessary in non-optional suites containing no other statements.
  If a suite contains another statement,
  adding ``pass`` is redundant.
  Docstrings count as a statement.

  Non-optional suites are the suites of,
  for example,
  ``def``,
  ``class``,
  and ``if``.
  ``else`` and ``finally`` suites are optional,
  and as such this is never necessary::

    if predicate():
        do_something()
    else:
        pass

    try:
        do_something()
    finally:
        pass

L208
  `Pokémon exception handling <http://c2.com/cgi/wiki?PokemonExceptionHandling>`_ is always a mistake.
  If the intent is *really* to catch and ignore exceptions,
  explicitly name *which* exception types to silence.

L209
  ``return``,
  ``del``,
  ``raise``,
  ``assert``,
  ``print`` (in python 2, without ``print_function``)
  ``yield``,
  and ``yield from``
  are statements,
  not functions,
  and as such,
  do not require parentheses.

  This is okay::

    return (
      a
      + b)

  And this is not::

    return(a + b)

L210
  Instead of intentionally relying on the side effects of
  ``map``,
  ``filter``,
  or a comprehension,
  write an explicit for loop.

  This is okay::

    for x in y:
        print(x)

  And this is not::

    map(print, y)

L211
  Using ``map`` or ``filter`` with a ``lambda`` as the first argument is always better written as list comprehension or generator expression.
  An expression is more readable and extensible,
  and less importantly,
  doesn't incur as much function call overhead.

L212
  Using ``@staticmethod`` is always wrong.
  The two most common situations are:

  - Wanting to do something with the class but without an instance,
    in which case ``@classmethod`` is the correct solution.
  - Wanting to 'namespace' a function on a class,
    but this isn't Java,
    so make it a module-scoped function instead.

  Using ``staticmethod`` on its own is not a problem;
  this is perfectly acceptable for testing purposes::

    from some_module import do_some_more_io, some_io


    def do_io():
        return some_io()


    class Spam(object):
        do_io = staticmethod(do_io)
        do_some_more_io = staticmethod(do_some_more_io)



L3: Formatting
--------------

L301
  Files must end with a trailing newline.

.. _long lines:

L302
  The line was too long.

  Lines greater than ``hard-max-line-length``
  (which is considered the "hard limit",
  and by default is 119 columns)
  are never allowed.
  Lines greater than ``max-line-length``
  (which is considered the "soft limit",
  and by default is 79 columns)
  are allowed if and only if the line contains above a certain percentage of string literals *or* comments.
  The percentages of both are not combined.
  The "certain percentage" allowed is ``permissive-bulkiness-percentage``,
  which by default is 67%.

  For all of the following examples,
  the soft limit is 15 columns,
  and the hard limit is 25 columns.

  Disallowed because,
  at 20 characters,
  the line exceeds the soft limit,
  and the whole line is only 15% string literals by character count::

    ultradignified = 'y'

  Allowed because the whole line is 80% string literals by character count::

    t = 'electroplating'

  Allowed because the whole line is 75% comments by character count::

    f()  # accreditation

  Disallowed because the whole line is 20% comments and 50% string literals by character count,
  and neither of those is at or above 67%::

    d = 'smallpox'  # ok

  Disallowed because the whole line is 26 characters long,
  which exceeds the hard limit::

    thyroparathyroidectomize()


  The ``hard-max-line-length`` and ``permissive-bulkiness-percentage`` can be configured;
  see the section Configuration_.

L303
  noqa_ is ignored,
  and as such,
  ``# noqa`` comments should be deleted to reduce pointless noise.


.. _flake8: https://flake8.readthedocs.org/en/stable/
.. _Napoleon: http://sphinx-doc.org/ext/napoleon.html
.. _reStructuredText fields: http://docutils.sourceforge.net/docs/user/rst/quickref.html#field-lists
.. _Implicit relative imports: https://www.python.org/dev/peps/pep-0328/#rationale-for-absolute-imports
