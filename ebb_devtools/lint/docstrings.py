import re

import enum
import parsley

from ebb_devtools.lint.errors import Errors


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


_grammar = parsley.makeGrammar(r"""

anythingButNewline = ~'\n' anything
line = <anythingButNewline+>

leadingIndentCount = ' '*:indent -> len(indent)
docstring =
    '\n' ^(blank first line)
    leadingIndentCount:indent
    (line ^(non-whitespace character on the first line)):firstLine
    '\n' ^(complete first line)
    ((' '{indent}) ^(line with consistent indentation) line:line '\n' -> line
    | '\n' ^(blank line) -> None
    )*:lines
    (' '{indent} end) ^(final line empty but for indentation)
-> (indent, [firstLine] + lines)

""", {})


def docstring_errors(purpose, docstring):
    try:
        indent, lines = _grammar(docstring).docstring()
    except parsley.ParseError as e:
        yield Errors.docstring_formatting_error, {
            'parse_error': e.formatReason(),
        }
        return

    if purpose == DocstringPurpose.test:
        m = _bad_test_docstring_starts.match(lines[0])
        if m is not None:
            yield Errors.test_docstring_prefix, {'prefix': m.group()}

    for line_offset, line in enumerate(lines, start=1):
        if line is None:
            continue
        m = _sphinx_info_fields.match(line)
        if m is not None:
            yield Errors.use_napoleon_in_docstrings, {'field': m.group(1)}
