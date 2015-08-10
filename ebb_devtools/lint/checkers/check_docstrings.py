import re

import enum

from ebb_devtools.lint.checkers.registration import register_checker
from ebb_devtools.lint.errors import Errors


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
     )[ ]
""")


class DocstringPurpose(enum.Enum):
    test = 'test'
    other = 'other'


def docstring_errors(purpose, docstring):
    raw_lines = docstring.splitlines()
    if len(raw_lines) < 3:
        yield Errors.docstring_formatting_error, {
            'parse_error': (
                'docstrings must have """, their text, and """ all on '
                'separate lines'),
        }
        return
    if raw_lines[0] != '"""':
        yield Errors.docstring_formatting_error, {
            'parse_error': '''a docstring's first line must be just """''',
        }
    initial_indent = _docstring_leading_indent.match(raw_lines[1])
    indent = initial_indent.end(1)
    if indent % 4 != 0:
        yield Errors.docstring_formatting_error, {
            'parse_error': 'docstring indentation must be a multiple of four',
            'line_offset': 1,
            'column': 0,
        }
    first_line = initial_indent.group(2)
    if not first_line:
        yield Errors.docstring_formatting_error, {
            'parse_error': 'docstrings must have text on the first line',
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
            'parse_error': 'docstrings must end with """',
            'line_offset': len(raw_lines) - 1,
            'column': indent,
        }

    if purpose == DocstringPurpose.test:
        m = _bad_test_docstring_starts.match(lines[0])
        if m is not None:
            yield Errors.test_docstring_prefix, {
                'prefix': m.group(),
                'line_offset': 1,
                'column': indent,
            }

    for line_offset, line in enumerate(lines, start=1):
        if line is None:
            continue
        m = _sphinx_info_fields.match(line)
        if m is not None:
            yield Errors.use_napoleon_in_docstrings, {
                'field': m.group(1),
                'line_offset': line_offset,
                'column': indent,
            }


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
