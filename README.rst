.. image:: https://img.shields.io/travis/flowroute/ebb-lint/master.svg?style=flat-square

.. image:: https://img.shields.io/coveralls/flowroute/ebb-lint/master.svg?style=flat-square

.. image:: https://img.shields.io/pypi/v/ebb-lint.svg?style=flat-square

.. image:: https://img.shields.io/pypi/l/ebb-lint.svg?style=flat-square


==========
 ebb-lint
==========

It's a `flake8`_ plugin!
It lints for style problems!
All you have to do to activate it is::

  $ pip install ebb-lint


Configuration
=============

Configuration does nothing but cause bugs or laxness,
so ``ebb-lint`` has none.

.. _one-off scripts:

If,
however,
one is writing a one-off script and wishes to use ``print`` against ``ebb-lint``\ 's wishes,
a comment can be added to the top of the file to disable that warning::

  # I sincerely swear that this is one-off code.

This comment must be above any statements in the code
(including docstrings),
on a line by itself.


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
  If you really intend to catch and ignore exceptions,
  explicitly name *which* exception types you wish to silence.


L3: Whitespace
--------------

L301
  Files must end with a trailing newline.


.. _flake8: https://flake8.readthedocs.org/en/stable/
.. _Napoleon: http://sphinx-doc.org/ext/napoleon.html
.. _reStructuredText fields: http://docutils.sourceforge.net/docs/user/rst/quickref.html#field-lists
.. _Implicit relative imports: https://www.python.org/dev/peps/pep-0328/#rationale-for-absolute-imports
