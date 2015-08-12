from __future__ import unicode_literals

import collections

import enum


Error = collections.namedtuple('Error', ['code', 'message'])


class Errors(enum.Enum):
    docstrings_category = Error(
        100, 'docstring-related errors')
    no_docstring_on_init = Error(
        101,
        "__init__ doesn't need a docstring; standard sphinx convention is to "
        "use the class-level docstring instead.")
    docstring_formatting_error = Error(
        102,
        'tried to validate the docstring: {parse_error}')
    test_docstring_prefix = Error(
        103,
        "don't start test docstrings with {prefix!r}")
    use_napoleon_in_docstrings = Error(
        104,
        'use sphinx.ext.napoleon instead of reST fields like :{field}:')

    dubious_syntax_category = Error(
        200, 'errors related to dubious syntax')
    no_trailing_comma_in_literal = Error(
        201,
        'container literals must have a trailing comma following the last '
        'element')
    no_print = Error(
        202,
        'print is only allowed while debugging; use logging in real code')
    no_debuggers = Error(
        203,
        'debuggers are only allowed while debugging; make sure to remove this '
        'before committing')
