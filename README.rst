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

If,
however,
one is writing a one-off script and wishes to use ``print`` against ``ebb-lint``\ 's wishes,
a comment can be added to the top of the file to disable that warning::

  # I sincerely swear that this is one-off code.

This comment must be above any statements in the code
(including docstrings),
on a line by itself.


.. _flake8: https://flake8.readthedocs.org/en/stable/
