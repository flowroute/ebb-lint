from __future__ import unicode_literals

import collections

import enum


Error = collections.namedtuple('Error', ['code', 'message'])


class Errors(enum.Enum):
    docstrings_category = Error(
        100, 'docstring-related errors')
    no_docstring_on_init = Error(
        101,
        ("__init__ doesn't need a docstring; standard sphinx convention is to "
         "use the class-level docstring instead."))
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
        ('container literals must have a trailing comma following the last '
         'element'))
    no_print = Error(
        202,
        'print is only allowed while debugging; use logging in real code')
    no_debuggers = Error(
        203,
        ('debuggers are only allowed while debugging; make sure to remove '
         'this before committing'))
    no_unintentional_implicit_concatenation = Error(
        204,
        ('implicit string literal concatenation requires all string literals '
         'to be enclosed in parentheses containing nothing but string '
         'literals'))
    no_definition_statements_in_dunder_init = Error(
        205,
        'do not define functions or classes in __init__.py')
    no_implicit_relative_imports = Error(
        206,
        'do not use implicit relative imports')
    useless_pass = Error(
        207,
        ("'pass' is only necessary in non-optional suites containing no other "
         "statements"))
    no_except_pass = Error(
        208,
        'be more specific about which exception types to silence')
    useless_parens = Error(
        209,
        '{stmt} is not a function; parentheses are not required')
    no_side_effects = Error(
        210,
        'use a for loop instead of using {thing} for its side effect')
    no_map_or_filter_with_lambda = Error(
        211,
        'use a comprehension instead of {func} with lambda')
    no_staticmethod_decorator = Error(
        212,
        '@staticmethod is always wrong; you probably want @classmethod')

    formatting_category = Error(
        300, 'errors related to formatting')
    no_trailing_newline = Error(
        301,
        'files must end with a trailing newline')
    line_too_long = Error(
        302,
        ('line too long ({length} > {which_limit} limit of {limit} '
         'characters{extra})'))
    no_noqa = Error(
        303,
        'noqa is ignored, so this comment is not useful')
