from __future__ import unicode_literals

import ast
import re

import pytest
import six

from ebb_lint.flake8 import EbbLint, Lines


py3skip = pytest.mark.skipif(six.PY3, reason='not runnable on python 3')


_code_pattern = re.compile(r"""
    (?x)
    \$([A-Z]\d{3})\$
""")


def find_error_locations(source):
    error_locations = []

    def replacement(match):
        last_offset = error_locations[-1][2] if error_locations else 0
        new_offset = last_offset + match.end() - match.start()
        error_locations.append((
            match.start() - last_offset, match.group(1), new_offset))
        return ''

    source = _code_pattern.sub(replacement, source)
    lines = Lines(source.splitlines(True))
    return source, [
        lines.position_of_byte(b) + (code,) for b, code, _ in error_locations]


@pytest.fixture(autouse=True, scope='session')
def scan_for_checkers():
    EbbLint.add_options(None)
    EbbLint.parse_options(None)


all_sources = [
    '',

    """

def f():
    $L102$'''
    spam
    '''

    """,

    """

def f():
    $L102$'''spam'''

    """,

    """

def f():
    $L102$'spam'

    """,

    """

def f():
    $L102$"spam"

    """,

    '''

def f():
    """$L102$ spam"""

    ''',

    '''

def f():
    """spam$L102$ """

    ''',

    '''

def __init__():
    $L101$"""
    spam
    """

    ''',

    '''

class Spam(object):
    """
    It's spam.
    """

    ''',

    '''

import $L203$pdb
pdb.$L203$set_trace()

    ''',

    '''

import $L203$pdb as not_pdb
not_pdb.$L203$set_trace()

    ''',

    '''

from $L203$pdb import set_trace
set_trace()

    ''',

    '''

import pudb
pudb.$L203$set_trace()

    ''',

    '''

x = $L204$'a' 'b'

    ''',

    '''

x = [
    $L204$'a'
    'b',
    'c',
]

    ''',

    '''

x = [
    ($L204$'a'
     'b'.format()),
    'c',
]

    ''',

    '''

x = [
    ($L204$'a'
     'b'()),
    'c',
]

    ''',

    '''

x = [
    [$L204$'a'
     'b'],
    'c',
]

    ''',

    '''

x = [
    ('a'
     'b').format(),
    'c',
]

    ''',

    '''

x = [
    ('a'
     'b'),
    'c',
]

    ''',

    '''

x = ('a' 'b')

    ''',

    '''

from __future__ import print_function
import sys

$L202$print("Yay!", file=sys.stdout)

    ''',

    '''

# I sincerely swear that this is one-off code.
from __future__ import print_function
import sys

print("Yay!", file=sys.stdout)

    ''',

    '''

def f():
    pass$L301$''',

    '''

# coding: utf-8
x = '\ufffd' + $L204$'\ufffe' '\uffff'

    ''',

    '''

def f():
    """
    Spam; eggs.
    """
    $L207$pass

    ''',

    '''

if True:
    pass
else:
    $L207$pass

    ''',

    '''

for x in y:
    pass
else:
    $L207$pass

    ''',

    '''

while True:
    pass
else:
    $L207$pass

    ''',

    '''

try:
    pass
finally:
    $L207$pass

    ''',

    '''

try:
    pass
except Whatever:
    do_something()
    $L207$pass

    ''',

    '''

try:
    pass
except:
    $L208$pass

    ''',

    '''

try:
    pass
except Whatever:
    pass

    ''',

    '''

try:
    pass
except Whatever:
    pass
except:
    $L208$pass

    ''',

    '''

try:
    pass
except:
    $L208$pass
except Whatever:
    pass

    ''',

    '''

try:
    pass
except:
    $L208$pass
else:
    do_something()
finally:
    do_something_else()

    ''',
]


contexts = [
    ('# I sincerely swear that this is one-off code.', ''),

    ("""
# I sincerely swear that this is one-off code.
# I sincerely swear that I am not a member of the Communist Party.
    """, ''),

    ('', '$L202$'),
]


all_sources.extend(
    py3skip('''
{ctx[0]}
{ctx[1]}{print_}
    '''.format(ctx=ctx, print_=print_))
    for ctx in contexts
    for print_ in [
        "print 'hi'",
        "print 'hi',",
        "print >> aether, 'hi'",
        "print",
    ])


all_sources.extend(
    '''
{ctx[0]}
from __future__ import print_function
{ctx[1]}{print_}
    '''.format(ctx=ctx, print_=print_)
    for ctx in contexts
    for print_ in [
        "print('hi')",
        "print()",
    ])


element_pairs = [
    ('1', '2'),
    ("'spam'", "'eggs'"),
]


delimiter_pairs = [
    (('(', ')'), ['f(x)']),
    (('[', ']'), ['f(x)']),
    (('{', '}'), ['f(x)', 'f(x): g(x)']),
]


all_sources.extend(
    template.format(delim=delim, elem=elem)
    for delim, _ in delimiter_pairs
    for elem in element_pairs
    for template in [
        '''

spam = {delim[0]}
    {elem[0]},
    {elem[1]},
{delim[1]}

        ''',

        '''

spam = {delim[0]}
    {elem[0]},
{delim[1]}

        ''',

        '''

spam = {delim[0]}
    {elem[0]},
    $L201${elem[1]}
{delim[1]}

        ''',

        '''

spam = {delim[0]}{elem[0]}, {elem[1]}{delim[1]}

        ''',

        '''

spam = {delim[0]}{elem[0]}{delim[1]}

        ''',
    ])


all_sources.extend(
    '''

spam = {delim[0]}
    $L201${elem[0]}
{delim[1]}

    '''.format(delim=delim, elem=elem)
    for delim, _ in delimiter_pairs
    for elem in element_pairs
    # Ignore this because it's a parenthesized expression, and not a tuple.
    if delim[0] != '(')


all_sources.extend(
    template.format(delim=delim)
    for delim, _ in delimiter_pairs
    for template in [
        '''

spam = {delim[0]}{delim[1]}

        ''',

        '''

spam = {delim[0]}
{delim[1]}

        ''',
    ])


all_sources.extend(
    template.format(delim=delim, expr=expr)
    for delim, exprs in delimiter_pairs
    for expr in exprs
    for template in [
        '''

spam = {delim[0]}
    {expr} for x in y
{delim[1]}

        ''',

        '''

spam = {delim[0]}
    {expr}
    for x in y
{delim[1]}

        ''',

        '''

spam = {delim[0]}
    {expr}
    for x in y
    if p(x)
{delim[1]}

        ''',

        '''

spam = {delim[0]}
    {expr}
    for y in z
    for x in y
    if p(x)
{delim[1]}

        ''',

        '''

spam = {delim[0]}
    {expr} for x in y{delim[1]}

        ''',

        '''

spam = {delim[0]}{expr} for x in y{delim[1]}

        ''',
    ])


dict_element_pairs = [
    (('1', '2'), ('3', '4')),
    (("'spam'", "'eggs'"), ("'eggs'", "'spam'")),
]


all_sources.extend(
    template.format(elem=elem)
    for elem in dict_element_pairs
    for template in [
        '''

spam = {{
    {elem[0][0]}: {elem[0][1]},
    {elem[1][0]}: {elem[1][1]},
}}

        ''',

        '''

spam = {{
    {elem[0][0]}: {elem[0][1]},
    {elem[1][0]}: $L201${elem[1][1]}
}}

        ''',

        '''

spam = {{{elem[0][0]}: {elem[0][1]}, {elem[1][0]}: {elem[1][1]}}}

        ''',
    ])


docstrings = [
    """
    hi
    """,

    """
    hi

    hello
    """,

    """
    hi

      hello

    hey
    """,

    """
        hi
        """,

    """
        hi

        hello
        """,

    """
        hi

          hello

        hey
        """,

    '\nhi\n',

    '\nhi\n\nhello\n',

    '\nhi\n\n  hello\n\nhey\n',

    """
    hi

$L102$  hey

    hello
    """,

    """
$L102$
    hi
    """,

    """
    $L102$
    hi
    """,

    '\n    hi\n$L102$',

    """
$L102$   hey
   """,

    """
$L102$   hey
   $L102$ """,

    'hi',
]


docstrings.extend("""
    $L104$:{} spam: eggs
    """.format(field) for field in [
    'param', 'parameter', 'arg', 'argument', 'key', 'keyword', 'type',
    'raises', 'raise', 'except', 'exception', 'var', 'ivar', 'cvar',
    'vartype', 'returns', 'return', 'rtype',
])


all_sources.extend('''

def f():
    """{}"""

'''.format(docstring) for docstring in docstrings)


all_sources.extend('''

def f():
    $L102$"""{}"""

'''.format(docstring) for docstring in [
    """
""",

    """
 """,

    """
hi""",

    """hi
    """,

    '',
])


test_docstrings = [
    """
    $L103$Test that the thing does the thing.
    """,

    '$L103$Test that the thing does the thing.',

    """
    $L103$VERIFY MY YELLING VOLUME
    """,

    """
    MY YELLING VOLUME IS FINE
    """,
]


test_docstrings.extend("""
    $L103${} a thing.
    """.format(word) for word in [
    'test', 'verify', 'ensure', 'tests', 'verifies', 'ensures', 'testing',
    'verifying', 'ensuring',
])


all_sources.extend('''

def test_f():
    """{}"""

'''.format(docstring) for docstring in test_docstrings)


dunder_init_sources = [
    '''

$L205$def spam():
    pass

    ''',

    '''

$L205$class Spam():
    pass

    ''',

    '''

from spam import eggs

__all__ = ['eggs']

    ''',
]


all_filename_sources = [
    ('__init__.py', source) for source in dunder_init_sources]


@pytest.fixture
def assert_lint():
    def check(source, sourcefile):
        # Strip trailing spaces, since the most comfortable triple-quoted
        # string format will have extra spaces on the last line. If this isn't
        # removed, it'll throw off the trailing newline checker.
        source = source.rstrip(' ')
        source, error_locations = find_error_locations(source)
        sourcefile.write_text(source, encoding='utf-8')
        lint = EbbLint(ast.parse(source), sourcefile.strpath)
        actual = [
            (line, col, message[:4]) for line, col, message, _ in lint.run()]
        assert actual == error_locations

    return check


@pytest.mark.parametrize(('filename', 'source'), all_filename_sources)
def test_linting_with_filename(assert_lint, tmpdir, source, filename):
    sourcefile = tmpdir.join(filename)
    assert_lint(source, sourcefile)


@pytest.mark.parametrize('source', all_sources)
def test_linting_with_default_filename(assert_lint, tmpdir, source):
    sourcefile = tmpdir.join('source.py')
    assert_lint(source, sourcefile)


implicit_relative_import_sources = [
    {
        'spam.py': '''

import $L206$eggs

        ''',

        'eggs.py': '''

import $L206$spam

        ''',
    },

    {
        'spam.py': '''

import eggs

        ''',
    },

    {
        'spam.py': '''

import $L206$eggs.eggs

        ''',

        'eggs/__init__.py': '',
        'eggs/eggs.py': '',
    },

    {
        'spam.py': '''

import eggs.eggs

        ''',
    },
]


implicit_relative_import_sources.extend(
    {
        'spam.py': '''

import $L206$eggs

        ''',

        'eggs.{}'.format(ext): '',
    }
    for ext in ['py', 'pyc', 'pyo', 'pyd', 'so']
)


implicit_relative_import_sources.extend(
    {
        'spam.py': '''

import $L206$eggs

        ''',

        'eggs/__init__.{}'.format(ext): '',
    }
    for ext in ['py', 'pyc', 'pyo']
)


all_implicit_relative_import_sources = [
    (name, sources)
    for sources in implicit_relative_import_sources
    for name in sources]


@pytest.mark.parametrize(
    ('to_test', 'sources'), all_implicit_relative_import_sources)
def test_linting_implicit_relative_imports(
        assert_lint, tmpdir, to_test, sources):
    for name, source in sources.items():
        tmpdir.join(name).write_text(source, encoding='utf-8', ensure=True)
    assert_lint(sources[to_test], tmpdir.join(to_test))
