from __future__ import unicode_literals

import collections
import re

import enum

from ebb_lint.checkers.registration import register_checker
from ebb_lint.errors import Errors


_single_line_docstring = re.compile(r'\A"""(\s*)(.*?)(\s*)"""\Z')

_docstring_leading_indent = re.compile(r'^( *)(.*)$')

_bad_test_docstring_starts = re.compile(r"""
    (?xi)
    \A(?:test|verify?|ensure?)(?:s|ies|ing)?\b
""")

_sphinx_info_fields = re.compile(r"""
    (?x)
    ^:
     (arg(?:ument)?
     |[ci]var
     |except(?:ion)?
     |key(?:word)?
     |param(?:eter)?
     |r(?:aises?|eturns?|type)
     |type
     |var(?:type)?
     )[: ]
""")


class DocstringPurpose(enum.Enum):
    test = 'test'
    other = 'other'


class Line(collections.namedtuple('Line', ['pos', 'line'])):
    def error(self, error, **extra):
        extra.update(self.pos)
        return error, extra


def docstring_errors(purpose, docstring):
    raw_lines = docstring.splitlines()
    if len(raw_lines) == 1:
        m = _single_line_docstring.match(raw_lines[0])
        if m is None:
            yield Errors.docstring_formatting_error, {
                'parse_error': (
                    'single-line docstrings must still start and end with '
                    '"""'),
            }
            return

        if not m.group(2):
            yield Errors.docstring_formatting_error, {
                'parse_error': 'single-line docstrings must not be empty',
            }
            return
        else:
            if m.group(1):
                yield Errors.docstring_formatting_error, {
                    'parse_error': (
                        'single-line docstrings must not start with '
                        'whitespace'),
                    'offset': m.start(1),
                }
            if m.group(3):
                yield Errors.docstring_formatting_error, {
                    'parse_error': (
                        'single-line docstrings must not end with whitespace'),
                    'offset': m.start(3),
                }

        lines = [
            Line({'offset': m.start(2)}, m.group(2)),
        ]

    elif len(raw_lines) < 3:
        yield Errors.docstring_formatting_error, {
            'parse_error': (
                'docstrings must have """, their text, and """ all on '
                'separate lines, or all on the same line'),
        }
        return

    else:
        if raw_lines[0] != '"""':
            yield Errors.docstring_formatting_error, {
                'parse_error': (
                    "a multi-line docstring's first line must be just " '"""'),
            }
            return
        initial_indent = _docstring_leading_indent.match(raw_lines[1])
        indent = initial_indent.end(1)
        if indent % 4 != 0:
            yield Errors.docstring_formatting_error, {
                'parse_error': (
                    'docstring indentation must be a multiple of four'),
                'line_offset': 1,
                'column': 0,
            }
        first_line = initial_indent.group(2)
        if not first_line:
            yield Errors.docstring_formatting_error, {
                'parse_error': (
                    'multi-line docstrings must have text on the first line '
                    'following the """'),
                'line_offset': 1,
                'column': indent,
            }
            return

        indent_string = initial_indent.group(1)
        lines = [first_line]
        all_lines_good = True
        for line_offset, raw_line in enumerate(raw_lines[2:], start=2):
            if not raw_line:
                lines.append(None)
            elif raw_line.startswith(indent_string):
                lines.append(raw_line[indent:])
            else:
                yield Errors.docstring_formatting_error, {
                    'parse_error': (
                        'every line of a docstring must have the same '
                        'indentation'),
                    'line_offset': line_offset,
                    'column': 0,
                }
                all_lines_good = False
                lines.append(None)

        if all_lines_good and lines[-1] != '"""':
            yield Errors.docstring_formatting_error, {
                'parse_error': 'multi-line docstrings must end with """',
                'line_offset': len(raw_lines) - 1,
                'column': indent,
            }

        lines = [
            Line({'line_offset': line_offset, 'column': indent}, line)
            for line_offset, line in enumerate(lines, start=1)]

    if purpose == DocstringPurpose.test:
        m = _bad_test_docstring_starts.match(lines[0].line)
        if m is not None:
            yield lines[0].error(
                Errors.test_docstring_prefix, prefix=m.group())

    for line in lines:
        if line.line is None:
            continue
        m = _sphinx_info_fields.match(line.line)
        if m is not None:
            yield line.error(
                Errors.use_napoleon_in_docstrings, field=m.group(1))


@register_checker(r"""

( classdef< which='class' name=NAME any*
            suite< '\n' TOKEN simple_stmt< docstring=STRING any > any* > >
| funcdef< which='def' name=NAME any*
           suite< '\n' TOKEN simple_stmt< docstring=STRING any > any* > >
)

""")
def check_docstring(which, name, docstring):
    purpose = DocstringPurpose.other
    if which.value == 'def':
        if name.value.startswith('test_'):
            purpose = DocstringPurpose.test
        elif name.value == '__init__':
            yield docstring, Errors.no_docstring_on_init, {}
    for error, kw in docstring_errors(purpose, docstring.value):
        yield docstring, error, kw
