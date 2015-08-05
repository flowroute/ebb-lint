import pytest

from ebb_devtools.lint.docstrings import DocstringPurpose, docstring_errors


@pytest.mark.parametrize('docstring', [
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
])
def test_correct_docstrings(docstring):
    assert list(docstring_errors(DocstringPurpose.other, docstring)) == []


@pytest.mark.parametrize('docstring', [
    """
    hi

  hey

    hello
    """,

    """hi
    """,

    """hi""",

    """
    hi""",

    """

    hi
    """,

    '',

    '\n',

    '\n ',

    '\n    ',

    '\n    hi\n',

    '\n    hi\n    \n    hello\n    ',
])
def test_incorrect_docstrings(docstring):
    assert list(docstring_errors(DocstringPurpose.other, docstring)) != []


@pytest.mark.parametrize('docstring', [
    """
    Test that the thing does the thing.
    """,

    """
    VERIFY MY YELLING VOLUME
    """,
])
def test_incorrect_test_docstrings(docstring):
    assert list(docstring_errors(DocstringPurpose.test, docstring)) != []


@pytest.mark.parametrize('word', [
    'test', 'verify', 'ensure', 'tests', 'verifies', 'ensures', 'testing',
    'verifying', 'ensuring',
])
def test_incorrect_test_docstring_stemming(word):
    docstring = """
    {} a thing.
    """.format(word)
    assert list(docstring_errors(DocstringPurpose.test, docstring)) != []


@pytest.mark.parametrize('field', [
    'param', 'parameter', 'arg', 'argument', 'key', 'keyword', 'type',
    'raises', 'raise', 'except', 'exception', 'var', 'ivar', 'cvar',
    'vartype', 'returns', 'return', 'rtype',
])
@pytest.mark.parametrize('purpose', DocstringPurpose)
def test_sphinx_fields(field, purpose):
    docstring = """
    :{} spam: eggs
    """.format(field)
    assert list(docstring_errors(purpose, docstring)) != []


@pytest.mark.parametrize('docstring', [
    """
    Do a thing.

    Parameters:
       spam (meat): To eat.
       eggs (dairy): To eat.
    """,
])
def test_napoleon_is_fine(docstring):
    assert list(docstring_errors(DocstringPurpose.other, docstring)) == []
