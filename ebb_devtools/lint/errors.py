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
